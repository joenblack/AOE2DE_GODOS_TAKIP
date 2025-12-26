from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base

class Player(Base):
    __tablename__ = "players"

    player_id = Column(String, primary_key=True, index=True) # Internal UUID or similar if needed, but usually profile_id is enough. Let's use profile_id as PK for simplicity or map it.
    # User request suggested: player_id (PK, internal UUID), steam_id, aoe_profile_id.
    # Let's follow the schema:
    # player_id (PK, internal UUID) - wait, if we process data from AoEStats, it uses profile_id heavily. 
    # Let's keep it simple: profile_id IS the ID for us unless we need multiple accounts per person.
    # User said: "player_id (PK, internal UUID), steam_id (unique, nullable), aoe_profile_id (unique)"
    # I will stick to user request.
    
    player_id = Column(String, primary_key=True) # generic ID
    steam_id = Column(String, unique=True, nullable=True)
    aoe_profile_id = Column(Integer, unique=True, nullable=False, index=True)
    display_name = Column(String)
    country = Column(String, nullable=True) # ISO 2 chars usually
    elo_rm_1v1 = Column(Integer, nullable=True)
    elo_rm_team = Column(Integer, nullable=True)
    last_match_at = Column(DateTime, nullable=True)
    
    added_at = Column(DateTime)
    last_seen_at = Column(DateTime)

    match_stats = relationship("MatchPlayer", back_populates="player", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    match_id = Column(BigInteger, primary_key=True, index=True) # Upstream gameId
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    ladder_type = Column(String, nullable=True) # RM1v1, RMTeam...
    map_id = Column(Integer, nullable=True)
    map_name = Column(String, nullable=True)
    patch_version = Column(String, nullable=True)
    
    # Robust Classification Flags
    is_1v1 = Column(Boolean, default=False, index=True)
    is_team_game = Column(Boolean, default=False, index=True)
    is_ranked = Column(Boolean, default=False, index=True)
    player_count = Column(Integer, default=0)
    team_count = Column(Integer, default=0)

    players = relationship("MatchPlayer", back_populates="match")


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(BigInteger, ForeignKey("matches.match_id"), index=True)
    aoe_profile_id = Column(Integer, ForeignKey("players.aoe_profile_id"), index=True)
    
    # Note: If player_id is PK in players, we should FK to that. 
    # But data comes with profile_id. Let's FK to aoe_profile_id (it must be unique in players).
    # SQLAlchemy requires the target column to be unique/pk. We set unique=True on aoe_profile_id.
    
    team = Column(Integer, nullable=True)
    civ_id = Column(Integer, nullable=True)
    civ_name = Column(String, nullable=True)
    result = Column(String, nullable=True) # W/L

    __table_args__ = (
        UniqueConstraint("match_id", "aoe_profile_id", name="uq_match_players_match_profile"),
        Index("ix_match_players_match_team", "match_id", "team"),
    )
    won = Column(Boolean, nullable=True)
    elo_before = Column(Integer, nullable=True)
    elo_after = Column(Integer, nullable=True)
    color = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)

    player = relationship("Player", back_populates="match_stats", primaryjoin="MatchPlayer.aoe_profile_id == Player.aoe_profile_id")
    match = relationship("Match", back_populates="players")

class AggPlayerDaily(Base):
    __tablename__ = "agg_player_daily"
    player_id = Column(String, ForeignKey("players.player_id"), primary_key=True)
    date = Column(DateTime, primary_key=True) # just date part
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    elo_end = Column(Integer, nullable=True) # day end ELO

class AggPlayerCiv(Base):
    __tablename__ = "agg_player_civ"
    player_id = Column(String, ForeignKey("players.player_id"), primary_key=True)
    civ_id = Column(Integer, primary_key=True)
    civ_name = Column(String, primary_key=True)
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_rate = Column(Integer, default=0) # percentage or float? Integer percent is simpler for display

class AggPlayerMap(Base):
    __tablename__ = "agg_player_map"
    player_id = Column(String, ForeignKey("players.player_id"), primary_key=True)
    map_id = Column(Integer, primary_key=True)
    map_name = Column(String, primary_key=True)
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_rate = Column(Integer, default=0)

class AggCombat(Base):
    """
    Stores synergy (teammate) and rivalry (opponent) stats.
    type: 'teammate' or 'opponent'
    """
    __tablename__ = "agg_combat"
    player_a_id = Column(String, ForeignKey("players.player_id"), primary_key=True)
    player_b_id = Column(String, ForeignKey("players.player_id"), primary_key=True)
    type = Column(String, primary_key=True) # teammate / opponent
    total_games = Column(Integer, default=0)
    wins_with = Column(Integer, default=0) # for teammate: wins together. for opponent: A beat B.
    # Note: wins_with for opponent means A beat B? or A won match where B was opponent?
    # Usually: A wins against B.
    win_rate = Column(Integer, default=0)

class RefCiv(Base):
    __tablename__ = "ref_civs"
    # civ_id is Fixed Key from game
    civ_id = Column(Integer, primary_key=True, autoincrement=False) 
    civ_name = Column(String, nullable=True)

class RefMap(Base):
    __tablename__ = "ref_maps"
    # map_id is Internal AutoIncrement
    map_id = Column(Integer, primary_key=True, autoincrement=True)
    map_name = Column(String, unique=True, nullable=False) # Name is unique identifier for us

