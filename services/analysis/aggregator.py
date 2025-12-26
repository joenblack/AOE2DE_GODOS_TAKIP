from sqlalchemy.orm import Session
from sqlalchemy import text, func, Integer
from ..db.models import MatchPlayer, Player, AggPlayerDaily, AggPlayerCiv, AggPlayerMap, AggCombat
import datetime

class Aggregator:
    def __init__(self, db: Session):
        self.db = db

    def refresh_daily_stats(self, player_id):
        # Calculate daily stats for a specific player
        # This is a naive implementation; normally we would do batch replace/upsert
        # For SQLite without specific UPSERT syntax support in basic SQL, we might delete and re-insert or use merge.
        pass

    def refresh_all(self):
        """
        Re-computes all analytical tables from scratch.
        TRUNCATE -> INSERT pattern is easiest for small datasets.
        """
        try:
            # 1. Clear aggregated tables (DROP/CREATE to handle schema changes and clean slate)
            # This is safer than delete() because we changed PK definitions in models.py
            tables_to_reset = [AggPlayerDaily, AggPlayerCiv, AggPlayerMap, AggCombat]
            for model in tables_to_reset:
                model.__table__.drop(self.db.bind, checkfirst=True)
                model.__table__.create(self.db.bind, checkfirst=True)
            
            # self.db.commit() # Create/Drop usually auto-commits in many engines, but commit here is safe.


            print("Aggregated tables cleared. Recomputing...")

            # 2. AggPlayerCiv
            # We need to join MatchPlayer with players table to get internal player_id
            # But wait, match_players stores aoe_profile_id. players table maps it to player_id.
            
            # Use raw SQL for bulk aggregate insert - it's faster and easier across DBs usually
            # But SQLite/Postgres syntax differs. Let's use Python logic with batch inserts for portability in this agent context.
            
            # Fetch all match_players joined with players
            results = self.db.query(
                Player.player_id, 
                MatchPlayer.civ_id, 
                MatchPlayer.civ_name, 
                func.count(MatchPlayer.match_id).label("total"),
                func.sum(func.cast(MatchPlayer.won, Integer)).label("wins")
            ).join(MatchPlayer, Player.aoe_profile_id == MatchPlayer.aoe_profile_id)\
             .group_by(Player.player_id, MatchPlayer.civ_id, MatchPlayer.civ_name).all()
            
            for r in results:
                # r is (player_id, civ_id, civ_name, total, wins)
                # handle None wins
                wins = r.wins if r.wins else 0
                total = r.total
                win_rate = int((wins / total) * 100) if total > 0 else 0
                
                agg = AggPlayerCiv(
                    player_id=r.player_id,
                    civ_id=r.civ_id or 0, # handle nulls
                    civ_name=r.civ_name or "Unknown",
                    total_games=total,
                    wins=wins,
                    win_rate=win_rate
                )
                self.db.add(agg)
            
            self.db.commit()
            print("AggPlayerCiv computed.")

            # 3. AggPlayerMap
            # Similar logic
            # Join MatchPlayer -> Match -> Player
            results_map = self.db.execute(text("""
                SELECT 
                    p.player_id, 
                    m.map_id, 
                    m.map_name, 
                    COUNT(mp.match_id) as total, 
                    SUM(CASE WHEN mp.won THEN 1 ELSE 0 END) as wins
                FROM match_players mp
                JOIN matches m ON mp.match_id = m.match_id
                JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
                GROUP BY p.player_id, m.map_id, m.map_name
            """)).fetchall()

            for r in results_map:
                wins = r.wins if r.wins else 0
                total = r.total
                win_rate = int((wins / total) * 100) if total > 0 else 0
                
                agg = AggPlayerMap(
                    player_id=r.player_id,
                    map_id=r.map_id or 0,
                    map_name=r.map_name or "Unknown",
                    total_games=total,
                    wins=wins,
                    win_rate=win_rate
                )
                self.db.add(agg)
            self.db.commit()
            print("AggPlayerMap computed.")

             # 4. AggPlayerDaily
            # We need date from started_at.
            # SQLite: strftime('%Y-%m-%d', started_at)
            # Postgres: started_at::date
            # Let's try flexible processing in python to be safe across distinct DBs
            
            # Fetch relevant data: player_id, started_at, won, elo_after
            raw_daily = self.db.execute(text("""
                SELECT 
                    p.player_id, 
                    m.started_at, 
                    mp.won,
                    mp.elo_after
                FROM match_players mp
                JOIN matches m ON mp.match_id = m.match_id
                JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
                WHERE m.started_at IS NOT NULL
                ORDER BY m.started_at ASC
            """)).fetchall()
            
            # Dictionary to aggregate in memory: keys (player_id, date_str)
            daily_stats = {} 
            
            for r in raw_daily:
                pid = r.player_id
                dt = r.started_at 
                if isinstance(dt, str):
                    try:
                        # Try parsing standard formats
                        # SQLite default is often "YYYY-MM-DD HH:MM:SS.ssssss" or similar
                        from dateutil.parser import parse
                        dt = parse(dt)
                    except ImportError:
                        # Fallback if dateutil not installed (it is in requirements? no, pandas is, but maybe not dateutil directly, though pandas installs it)
                        # requirements.txt had pandas.
                        # Simple fallback
                        if " " in dt:
                            dt = datetime.datetime.strptime(dt.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        else:
                            dt = datetime.datetime.strptime(dt, "%Y-%m-%d")
                
                date_only = dt.date() if dt else None
                if not date_only: continue

                won = 1 if r.won else 0
                elo = r.elo_after
                
                key = (pid, date_only)
                if key not in daily_stats:
                    daily_stats[key] = {'total': 0, 'wins': 0, 'last_elo': 0}
                
                daily_stats[key]['total'] += 1
                daily_stats[key]['wins'] += won
                if elo:
                    daily_stats[key]['last_elo'] = elo
            
            for (pid, d), val in daily_stats.items():
                agg = AggPlayerDaily(
                    player_id=pid,
                    date=d,
                    total_games=val['total'],
                    wins=val['wins'],
                    elo_end=val['last_elo']
                )
                self.db.add(agg)
            
            self.db.commit()
            print("AggPlayerDaily computed.")

            # 5. AggCombat (Teammates & Opponents)
            # Fetch all players per match: match_id, player_id, team, won
            combat_data = self.db.execute(text("""
                SELECT 
                    mp.match_id,
                    p.player_id,
                    mp.team,
                    mp.won
                FROM match_players mp
                JOIN players p ON mp.aoe_profile_id = p.aoe_profile_id
                WHERE mp.team IS NOT NULL
            """)).fetchall()

            # Group by match_id
            from collections import defaultdict
            match_groups = defaultdict(list)
            for r in combat_data:
                match_groups[r.match_id].append(r)
            
            # Aggregate
            # Key: (p1, p2, type) -> {total, wins}
            combat_stats = {}

            for mid, players in match_groups.items():
                # Generate pairs
                n = len(players)
                for i in range(n):
                    for j in range(n):
                        if i == j: continue
                        
                        p1 = players[i]
                        p2 = players[j]
                        
                        p1_id = p1.player_id
                        p2_id = p2.player_id
                        
                        # Teammate
                        if p1.team == p2.team:
                            k = (p1_id, p2_id, 'teammate')
                            if k not in combat_stats: combat_stats[k] = {'total': 0, 'wins': 0}
                            combat_stats[k]['total'] += 1
                            if p1.won: # if p1 won, p2 also won usually (team game)
                                combat_stats[k]['wins'] += 1
                        
                        # Opponent
                        else:
                            k = (p1_id, p2_id, 'opponent')
                            if k not in combat_stats: combat_stats[k] = {'total': 0, 'wins': 0}
                            combat_stats[k]['total'] += 1
                            if p1.won:
                                combat_stats[k]['wins'] += 1
            
            # Bulk Insert
            for (p1, p2, c_type), val in combat_stats.items():
                total = val['total']
                wins = val['wins']
                win_rate = int((wins / total) * 100) if total > 0 else 0
                
                agg = AggCombat(
                    player_a_id=p1,
                    player_b_id=p2,
                    type=c_type,
                    total_games=total,
                    wins_with=wins,
                    win_rate=win_rate
                )
                self.db.add(agg)
            
            self.db.commit()
            print("AggCombat computed.")
            
        except Exception as e:
            self.db.rollback()
            print(f"Error in aggregation: {e}")
            raise e
