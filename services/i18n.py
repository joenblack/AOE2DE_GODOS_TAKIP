
# Dictionary for translations
# Format: "key": {"en": "English Text", "tr": "Turkish Text"}

# Default language
DEFAULT_LANG = "tr"

TRANSLATIONS = {
    # --- SIDEBAR ---
    "sidebar.language": {"en": "Language", "tr": "Dil"},
    "sidebar.nav_title": {"en": "Navigation", "tr": "Navigasyon"},
    "sidebar.home": {"en": "Home", "tr": "Ana Sayfa"},
    "sidebar.overview": {"en": "Group Overview", "tr": "Grup Özeti"},
    "sidebar.profile": {"en": "Player Profile", "tr": "Oyuncu Profili"},
    "sidebar.matchups": {"en": "Matchups & Rivals", "tr": "Eşleşmeler & Rakipler"},
    "sidebar.synergy": {"en": "Team Synergy", "tr": "Takım Sinerjisi"},
    "sidebar.league": {"en": "Seasons & League", "tr": "Sezonlar & Lig"},
    "sidebar.compare": {"en": "Compare Players", "tr": "Oyuncu Karşılaştır"},
    "sidebar.admin": {"en": "Admin Settings", "tr": "Yönetici Ayarları"},
    "sidebar.filters": {"en": "Filters", "tr": "Filtreler"},
    "sidebar.refresh": {"en": "Update Data", "tr": "Veriyi Güncelle"},
    
    # --- COMMON ---
    "common.loading": {"en": "Loading...", "tr": "Yükleniyor..."},
    "common.no_data": {"en": "No data found.", "tr": "Veri bulunamadı."},
    "common.error": {"en": "Error", "tr": "Hata"},
    "common.success": {"en": "Success", "tr": "Başarılı"},
    "common.all": {"en": "All", "tr": "Tümü"},
    "common.wins": {"en": "Wins", "tr": "Galibiyet"},
    "common.losses": {"en": "Losses", "tr": "Mağlubiyet"},
    "common.games": {"en": "Games", "tr": "Maçlar"},
    "common.rank": {"en": "Rank", "tr": "Sıra"},
    "common.win_rate": {"en": "Win Rate", "tr": "Kazanma Oranı"},
    "common.date": {"en": "Date", "tr": "Tarih"},
    "common.duration": {"en": "Duration", "tr": "Süre"},
    "common.map": {"en": "Map", "tr": "Harita"},
    "common.civ": {"en": "Civilization", "tr": "Medeniyet"},
    "common.player": {"en": "Player", "tr": "Oyuncu"},
    "common.opponent": {"en": "Opponent", "tr": "Rakip"},
    "common.overall": {"en": "Overall", "tr": "Genel"},
    "common.days": {"en": "Days", "tr": "Gün"},
    "common.player_name": {"en": "Player Name", "tr": "Oyuncu Adı"},
    
    # --- FILTERS ---
    "filter.ladder": {"en": "Ladder Mode", "tr": "Oyun Modu"},
    "filter.time_period": {"en": "Time Period", "tr": "Zaman Aralığı"},
    "filter.all_time": {"en": "All Time", "tr": "Tüm Zamanlar"},
    "filter.last_30": {"en": "Last 30 Days", "tr": "Son 30 Gün"},
    "filter.last_90": {"en": "Last 90 Days", "tr": "Son 90 Gün"},
    "filter.last_180": {"en": "Last 6 Months", "tr": "Son 6 Ay"},
    
    # --- HOME ---
    "home.title": {"en": "AOE2 GODOŞ ELO TRACKER", "tr": "AOE2 GODOŞ ELO TAKİP"},
    "home.welcome": {"en": "Welcome to the group statistics dashboard!", "tr": "Grup istatistik paneline hoş geldiniz!"},
    "home.intro": {"en": "Use the sidebar to navigate between different analysis pages.", "tr": "Farklı analiz sayfaları arasında gezinmek için sol menüyü kullanın."},
    "home.recent_matches": {"en": "Recent Matches", "tr": "Son Maçlar"},
    
    # --- OVERVIEW ---
    "overview.title": {"en": "Group Overview", "tr": "Grup Genel Bakış"},
    "overview.leaderboard": {"en": "Leaderboard", "tr": "Liderlik Tablosu"},
    "overview.power_rankings": {"en": "Power Rankings (Recent Form)", "tr": "Güç Sıralaması (Form)"},
    "overview.hall_of_fame": {"en": "Hall of Fame", "tr": "Şöhretler Listesi"},
    "overview.form_rating": {"en": "Form Rating", "tr": "Form Puanı"},
    "overview.sos": {"en": "Strength of Schedule", "tr": "Fikstür Zorluğu"},
    "overview.upsets": {"en": "Upset Wins", "tr": "Sürpriz Galibiyetler"},
    "overview.marathoner": {"en": "Marathoner (Longest Match)", "tr": "Maratoncu (En Uzun Maç)"},
    "overview.speedrunner": {"en": "Speedrunner (Fastest Win)", "tr": "Hız Tutkunu (En Hızlı Win)"},
    "overview.streak_king": {"en": "Streak King (Max Win Streak)", "tr": "Seri Katil (En Uzun Galibiyet Serisi)"},
    "overview.giant_slayer": {"en": "Giant Slayer (Max Upsets)", "tr": "Dev Avcısı (En Çok Sürpriz)"},
    "overview.tooltip_form_rating": {"en": "Performance Rating based on last 20 games (Opp Elo + 400*(W-L)/N)", "tr": "Son 20 maça dayalı Performans Puanı (Rakip ELO + 400*(G-M)/N)"},
    "overview.tooltip_sos": {"en": "Strength of Schedule: Average Opponent ELO", "tr": "Fikstür Zorluğu: Ortalama Rakip ELO'su"},
    "overview.fun_zone": {"en": "Fun Zone: ELO Arena & Stats", "tr": "Eğlence Alanı: ELO Arenası & İstatistikler"},
    "overview.elo_gladiators": {"en": "ELO Gladiators", "tr": "ELO Gladyatörleri"},
    "overview.victory_share": {"en": "Victory Share", "tr": "Galibiyet Payı"},

    # --- PLAYER PROFILE ---
    "profile.select_player": {"en": "Select Player", "tr": "Oyuncu Seç"},
    "profile.tabs.overview": {"en": "Overview", "tr": "Özet"},
    "profile.tabs.maps_civs": {"en": "Maps & Civs", "tr": "Haritalar & Medeniyetler"},
    "profile.tabs.matchups": {"en": "Matchups", "tr": "Eşleşmeler"},
    "profile.tabs.timings": {"en": "Timings & Activity", "tr": "Zamanlama & Aktivite"},
    "profile.stats.total_games": {"en": "Total Games", "tr": "Toplam Maç"},
    "profile.stats.current_elo": {"en": "Current ELO (1v1)", "tr": "Güncel ELO (1v1)"},
    "profile.stats.max_elo": {"en": "Max ELO", "tr": "Maksimum ELO"},
    "profile.stats.best_civ": {"en": "Best Civ", "tr": "En İyi Civ"},
    "profile.fav_civ": {"en": "Favorite Civ", "tr": "Favori Civ"},
    "profile.fav_map": {"en": "Favorite Map", "tr": "Favori Harita"},
    "profile.nemesis": {"en": "Nemesis", "tr": "Baş Belası (Nemesis)"},
    "profile.prey": {"en": "Favorite Prey", "tr": "Kolay Lokma"},
    "profile.most_played": {"en": "Most Played Opponent", "tr": "En Çok Oynanan Rakip"},
    
    # --- RIVALRY (MATCHUPS) ---
    "rivalry.title": {"en": "Head-to-Head Rivalries", "tr": "Birebir Rekabetler"},
    "rivalry.player_a": {"en": "Player A", "tr": "1. Oyuncu"},
    "rivalry.player_b": {"en": "Player B", "tr": "2. Oyuncu"},
    "rivalry.select_players": {"en": "Select two different players to view head-to-head stats.", "tr": "Karşılaştırma için iki farklı oyuncu seçin."},
    "rivalry.streak": {"en": "Current Streak", "tr": "Mevcut Seri"},
    "rivalry.trend": {"en": "Win Rate Trend", "tr": "Kazanma Oranı Trendi"},
    "rivalry.clutch": {"en": "Clutch Index", "tr": "Clutch İndeksi (Kritik Anlar)"},
    
    # --- SYNERGY ---
    "synergy.title": {"en": "Team Synergy Score", "tr": "Takım Sinerji Skoru"},
    "synergy.desc": {"en": "Analyze how well players perform together compared to their individual standards.", "tr": "Oyuncuların birlikte performansını bireysel standartlarına göre analiz edin."},
    "synergy.caption": {"en": "Score = (Actual Duo Win Rate) - (Expected Win Rate based on individual Team ELO/WR)", "tr": "Skor = (Gerçek Duo Kazanma Oranı) - (Bireysel Takım ELO/KO Beklentisi)"},
    "synergy.top_synergy": {"en": "Top Synergy (Chemistry)", "tr": "En İyi Sinerji (Kimya)"},
    "synergy.comp_analysis": {"en": "Team Composition Analysis", "tr": "Takım Kompozisyon Analizi"},
    "synergy.duo": {"en": "Duo", "tr": "İkili"},
    "synergy.actual_wr": {"en": "Actual WR", "tr": "Gerçek KO"},
    "synergy.expected_wr": {"en": "Expected WR", "tr": "Beklenen KO"},
    "synergy.score": {"en": "Synergy Score", "tr": "Sinerji Skoru"},

    # --- LEAGUE ---
    "league.title": {"en": "Seasons & Mini-League", "tr": "Sezonlar & Mini Lig"},
    "league.desc": {"en": "Track weekly/monthly performance and simulate playoff outcomes based on current form.", "tr": "Haftalık/aylık performans takibi ve mevcut forma dayalı playoff simülasyonu."},
    "league.season_duration": {"en": "Season Duration", "tr": "Sezon Süresi"},
    "league.league_table": {"en": "League Table", "tr": "Lig Tablosu"},
    "league.playoff_sim": {"en": "Playoff Simulation", "tr": "Playoff Simülasyonu"},
    "league.playoff_desc": {"en": "Simulating a hypothetical tournament among the Top 4 players based on current FORM (ELO).", "tr": "Mevcut forma (ELO) dayalı olarak İlk 4 oyuncu arasında varsayımsal turnuva simülasyonu."},
    "league.summary": {"en": "Weekly Highlights Report", "tr": "Haftalık Özet Raporu"},
    "league.points": {"en": "Points", "tr": "Puan"},
    "league.win_prob": {"en": "Win Probability", "tr": "Kazanma Olasılığı"},
    "league.this_week": {"en": "This Week", "tr": "Bu Hafta"},
    "league.last_week": {"en": "Last Week", "tr": "Geçen Hafta"},
    "league.this_month": {"en": "This Month", "tr": "Bu Ay"},
    "league.last_month": {"en": "Last Month", "tr": "Geçen Ay"},
    "league.all_time": {"en": "All Time", "tr": "Tüm Zamanlar"},
    
    "league.warn_3players": {"en": "Need 4 players for semi-finals simulation. Simulating Top 2 match only.", "tr": "Yarı final simülasyonu için 4 oyuncu gerekiyor. Sadece İlk 2 maçı simüle ediliyor."},
    "league.sim_caption": {"en": "Based on {n} Monte Carlo simulations using current 1v1 ELO.", "tr": "Güncel 1v1 ELO kullanılarak yapılan {n} Monte Carlo simülasyonuna dayanmaktadır."},
    "league.average": {"en": "Ave", "tr": "Av"},
    
    # --- ANALYTICS ---
    "analytics.title": {"en": "Analytics Explorer", "tr": "Analiz Gezgini"},
    "analytics.elo_race": {"en": "ELO Racing Bar Chart", "tr": "ELO Yarışı Grafiği"},
    "analytics.map_stats": {"en": "Map Statistics", "tr": "Harita İstatistikleri"},
    "analytics.raw_data": {"en": "Raw Match Data", "tr": "Ham Maç Verisi"},
    "analytics.play_count": {"en": "Play Count by Map", "tr": "Haritaya Göre Oynanma Sayısı"},
    "analytics.most_played": {"en": "Most Played Maps", "tr": "En Çok Oynanan Haritalar"},
    "analytics.win_rate": {"en": "Win Rate by Map", "tr": "Haritaya Göre Kazanma Oranı"},
    "analytics.top_5": {"en": "Top 5 Maps Data:", "tr": "Top 5 Harita Verisi:"},
    "analytics.footer_note": {"en": "Win count here sums all players, so ratio is always ~50%. Requires player filter for meaningful winrate.", "tr": "Buradaki galibiyet sayısı tüm oyuncuları toplar, bu yüzden oran her zaman ~%50'dir. Anlamlı bir kazanma oranı için oyuncu filtresi gerekir."},
    
    # --- COMPARE ---
    "compare.title": {"en": "Player Comparison", "tr": "Oyuncu Karşılaştırma"},
    "compare.desc": {"en": "Compare general stats, playstyles, and trends side-by-side.", "tr": "Genel istatistikleri, oyun tarzlarını ve trendleri yan yana karşılaştırın."},
    "compare.most_played_civs": {"en": "Most Played Civs", "tr": "En Çok Oynanan Medeniyetler"},
    
    # --- ADMIN ---
    "admin.title": {"en": "Admin Settings", "tr": "Yönetici Ayarları"},
    "admin.data_management": {"en": "Data Management", "tr": "Veri Yönetimi"},
    "admin.trigger_update": {"en": "Trigger Daily Update Now", "tr": "Günlük Güncellemeyi Şimdi Başlat"},
    "admin.updating": {"en": "Fetching match history from WorldsEdgeLink and refreshing aggregates...", "tr": "WorldsEdgeLink'ten maç geçmişi çekiliyor ve veriler güncelleniyor..."},
    "admin.update_diagnostics": {"en": "Update Diagnostics", "tr": "Güncelleme Raporu"},
    "admin.update_issues": {"en": "Update completed with issues.", "tr": "Güncelleme sorunlarla tamamlandı."},
    "admin.update_success": {"en": "Update completed successfully.", "tr": "Güncelleme başarıyla tamamlandı."},
    "admin.manual_trigger_info": {"en": "This manually triggers the match-history pull and recomputes aggregates.", "tr": "Bu işlem maç geçmişini manuel olarak çeker ve hesaplamaları yeniler."},
    "admin.player_management": {"en": "Player Management", "tr": "Oyuncu Yönetimi"},
    "admin.add_player_title": {"en": "Add New Player to Watchlist", "tr": "İzleme Listesine Yeni Oyuncu Ekle"},
    "admin.add_player_btn": {"en": "Add Player", "tr": "Oyuncu Ekle"},
    "admin.add_player": {"en": "Add New Player", "tr": "Yeni Oyuncu Ekle"},
    "admin.close_diagnostics": {"en": "Close Diagnostics", "tr": "Raporu Kapat"},
    "admin.edit_remove": {"en": "Edit / Remove Player", "tr": "Oyuncuyu Düzenle / Sil"},
    
    # --- COMMON / CHART LABELS ---
    "label.features": {"en": "Features", "tr": "Özellikler"},
    "label.recent_activity": {"en": "Recent Activity", "tr": "Son Aktiviteler"},
    "label.last_match": {"en": "Last Match", "tr": "Son Maç"},
    "label.matchup": {"en": "Matchup", "tr": "Eşleşme"},
    "label.current_elo": {"en": "Current ELO", "tr": "Güncel ELO"},
    "label.at_a_glance": {"en": "At a Glance", "tr": "Özet Bakış"},
    
    # --- INSIGHTS ---
    "insight.hot_streak": {"en": "Hot Streak: {win_rate}% WR in last {games} games", "tr": "Sıcak Seri: Son {games} maçta %{win_rate} KO"},
    "insight.strongest_early": {"en": "Strongest in Early Game: {win_rate}% WR", "tr": "Erken Oyunda Güçlü: %{win_rate} KO"},
    "insight.map_specialist": {"en": "Map Specialist: {map_name} ({win_rate}% WR)", "tr": "Harita Uzmanı: {map_name} (%{win_rate} KO)"},
    "insight.confidence": {"en": "Confidence Interval: Actual skill likely between {low}% - {high}%", "tr": "Güven Aralığı: Gerçek beceri muhtemelen %{low} - %{high} arasında"},
    
    # --- CHART TITLES ---
    "chart.match_timeline": {"en": "Match Timeline", "tr": "Maç Zaman Çizelgesi"},
    "chart.match_history": {"en": "Match History (Duration vs Date)", "tr": "Maç Geçmişi (Süre vs Tarih)"},
    "chart.result_period": {"en": "Result, Period", "tr": "Sonuç, Dönem"},
    "chart.win_mid": {"en": "Win, Mid", "tr": "Galibiyet, Orta"},
    "chart.loss_mid": {"en": "Loss, Mid", "tr": "Mağlubiyet, Orta"},
    "chart.win_late": {"en": "Win, Late", "tr": "Galibiyet, Geç"},
    "chart.loss_late": {"en": "Loss, Late", "tr": "Mağlubiyet, Geç"},
    "chart.win_early": {"en": "Win, Early", "tr": "Galibiyet, Erken"},
    "chart.loss_early": {"en": "Loss, Early", "tr": "Mağlubiyet, Erken"},

    # --- RIVALRY / SYNERGY TABLES ---
    "table.perf_context": {"en": "Performance Context", "tr": "Performans Bağlamı"},
    "table.civ_matchups": {"en": "Civ Matchups", "tr": "Civ Eşleşmeleri"},
    "table.map_stats": {"en": "Map Stats", "tr": "Harita İstatistikleri"},
    "table.recent_matches": {"en": "Recent Matches", "tr": "Son Maçlar"},
    "table.result": {"en": "Result", "tr": "Sonuç"},
    "table.saved_at": {"en": "Played on {date} as {civ}", "tr": "{date} tarihinde {civ} olarak oynandı"},
    
    # --- SYNERGY ---
    "synergy.highest_wr": {"en": "Highest Duo Win Rate", "tr": "En Yüksek Duo Kazanma Oranı"},
    "synergy.lowest_wr": {"en": "Lowest Duo Win Rate", "tr": "En Düşük Duo Kazanma Oranı"},
    "synergy.best_combo": {"en": "Best Combo", "tr": "En İyi Kombo"},
    "synergy.weakest_combo": {"en": "Weakest Combo", "tr": "En Zayıf Kombo"},
    "synergy.role_analysis": {"en": "Which civilization role combinations work best? (Derived from tracked team games)", "tr": "Hangi medeniyet rol kombinasyonları en iyi sonucu veriyor? (Takım oyunlarından türetilmiştir)"},
    "synergy.composition": {"en": "Composition", "tr": "Kompozisyon"},
    "synergy.avg": {"en": "avg", "tr": "ort"},
    
    # --- OVERVIEW SUBTEXT ---
    "overview.subtext": {"en": "Celebrating the extremes: Speed, Endurance, Improvement, and Upsets.", "tr": "Uç noktaları kutluyoruz: Hız, Dayanıklılık, Gelişim ve Sürprizler."},
    "profile.subtitle": {"en": "Detailed breakdown of player performance with statistical guardrails.", "tr": "İstatistiksel sınırlar dahilinde detaylı oyuncu performansı analizi."},
    
    # --- DURATION ANALYSIS ---
    "duration.title": {"en": "Game Duration Analysis", "tr": "Oyun Süresi Analizi"},
    "duration.win_rate_phase": {"en": "Win Rate by Phase (with 95% Confidence Interval)", "tr": "Evreye Göre Kazanma Oranı (%95 Güven Aralığı ile)"},
    "duration.early": {"en": "Early (<20m)", "tr": "Erken (<20dk)"},
    "duration.mid": {"en": "Mid (20-35m)", "tr": "Orta (20-35dk)"},
    "duration.late": {"en": "Late (35m+)", "tr": "Geç (35dk+)"},
    
    # --- MATCHUP DESC ---
    "matchup.need_civ_games": {"en": "Need {min} games against a civ.", "tr": "Bir medeniyete karşı en az {min} maç gerekli."},
    "matchup.most_difficult": {"en": "Most Difficult Matchups", "tr": "En Zor Eşleşmeler"},
    "matchup.easiest": {"en": "Easiest Matchups", "tr": "En Kolay Eşleşmeler"},
    "matchup.specific_players": {"en": "Performance against specific players.", "tr": "Belirli oyunculara karşı performans."},
    "admin.watchlist": {"en": "Watchlist", "tr": "İzleme Listesi"},
    "admin.ref_data": {"en": "Reference Data (Mappings)", "tr": "Referans Veri (Eşleştirmeler)"},
    "admin.ref_civs": {"en": "Civilizations", "tr": "Medeniyetler"},
    "admin.ref_maps": {"en": "Maps", "tr": "Haritalar"},
    "admin.only_missing": {"en": "Show only missing/unknown", "tr": "Sadece eksik/bilinmeyenleri göster"},
    "admin.fix_names_title": {"en": "Fix Missing Names", "tr": "Eksik İsimleri Düzelt"},
    "admin.fix_names_btn": {"en": "Find and Resolve Missing Player Names", "tr": "Eksik İsimleri Bul ve Çöz"},
    "admin.fix_names_info": {"en": "Scanning for players with missing names...", "tr": "Eksik ismi olan oyuncular taranıyor..."},
    "admin.player_images": {"en": "Player Images", "tr": "Oyuncu Resimleri"},
    "admin.upload_image": {"en": "Upload Player Image", "tr": "Oyuncu Resmi Yükle"},
    "admin.upload_btn": {"en": "Save Image", "tr": "Resmi Kaydet"},
    "admin.data_repair": {"en": "Data Repair Tool (Advanced)", "tr": "Veri Onarım Aracı (Gelişmiş)"},
    "admin.data_repair_warn": {"en": "This tool deduplicates match_players and adds a UNIQUE constraint. Run only once if you suspect data duplication.", "tr": "Bu araç mükerrer kayıtları temizler ve TEKİLLİK kuralı ekler. Veri tekrarından şüpheleniyorsanız sadece bir kez çalıştırın."},
    "admin.data_repair_btn": {"en": "Fix Duplicates & Add Constraint", "tr": "Mükerrerleri Düzelt & Kural Ekle"},
    "admin.data_repair_success": {"en": "Operation Complete! Cleared {count} duplicates. Unique Index ensured.", "tr": "İşlem Tamamlandı! {count} mükerrer kayıt temizlendi. Tekillik sağlandı."},
    "synergy.min_games": {"en": "Minimum Team Games Together", "tr": "Birlikte En Az Takım Maçı"},
    "synergy.min_games_warning": {"en": "Need at least 2 tracked players to calculate synergy.", "tr": "Sinerji hesaplamak için en az 2 takipli oyuncu gerekiyor."},
    "analytics.col_date": {"en": "Date", "tr": "Tarih"},
    "analytics.col_player": {"en": "Player", "tr": "Oyuncu"},
    "analytics.col_elo": {"en": "ELO", "tr": "ELO"},
    "analytics.col_map": {"en": "Map", "tr": "Harita"},
    "analytics.col_civ": {"en": "Civilization", "tr": "Medeniyet"},
    "analytics.col_result": {"en": "Result", "tr": "Sonuç"},
    "analytics.download_csv": {"en": "Download CSV", "tr": "CSV İndir"},
    "analytics.visualizing_elo": {"en": "Visualizing ELO progression over time.", "tr": "Zaman içindeki ELO gelişimini görselleştirme."},
    "common.select_chart": {"en": "Select Chart Metric", "tr": "Grafik Metriği Seç"},
    "common.unknown": {"en": "Unknown", "tr": "Bilinmiyor"},
    "league.min_games_filter": {"en": "Min Games:", "tr": "Min Maç:"},
    "league.no_playoff_data": {"en": "Not enough data for Playoff Sim.", "tr": "Playoff Simülasyonu için yeterli veri yok."},
    "admin.select_player_img": {"en": "Select Player", "tr": "Oyuncu Seç"},
    "admin.choose_image": {"en": "Choose an image...", "tr": "Bir resim seçin..."},
    "admin.saved_image": {"en": "Saved image for {name}!", "tr": "{name} için resim kaydedildi!"},
    "admin.save_civs": {"en": "Save Civilizations", "tr": "Medeniyetleri Kaydet"},
    "admin.save_maps": {"en": "Save Maps", "tr": "Haritaları Kaydet"},
    "admin.updated_rows": {"en": "Updated {count} rows.", "tr": "{count} satır güncellendi."},
    "admin.resolved_names": {"en": "Resolved names for {count} players.", "tr": "{count} oyuncunun ismi çözüldü."},
    "admin.no_missing_names": {"en": "No players found with missing names.", "tr": "Eksik ismi olan oyuncu bulunamadı."},
    "profile.edit_player": {"en": "Edit Player", "tr": "Oyuncuyu Düzenle"},
    "profile.save_changes": {"en": "Save Changes", "tr": "Değişiklikleri Kaydet"},
    "profile.remove_player": {"en": "Remove Player", "tr": "Oyuncuyu Sil"},
    "profile.updated": {"en": "Updated player.", "tr": "Oyuncu güncellendi."},
    "profile.removed": {"en": "Removed player.", "tr": "Oyuncu silindi."},
    # Newly added keys
    "profile.hot_streak": {"en": "🔥 Hot Streak", "tr": "🔥 Sıcak Seri"},
    "profile.cold_streak": {"en": "❄️ Cold Streak", "tr": "❄️ Soğuk Seri"},
    "profile.stable": {"en": "Stable", "tr": "İstikrarlı"},
    "profile.strongest_early": {"en": "Strongest in Early Game", "tr": "En İyi: Erken Oyun"},
    "profile.strongest_in": {"en": "Strongest in", "tr": "En İyi Dönem"},
    "profile.best_worst": {"en": "Best & Worst", "tr": "En İyi & En Kötü"},
    "profile.display_wr": {"en": "Display WR", "tr": "Görünen KO"},
    "profile.ci_moe": {"en": "CI_MoE", "tr": "Hata Payı"},
    "profile.no_maps_min": {"en": "No maps with {min}+ games.", "tr": "{min}+ maçı olan harita yok."},
    "profile.maps_insufficient": {"en": "Maps with < {min} games (Insufficient Data)", "tr": "{min}'den az maç yapılan haritalar (Yetersiz)"},
    "profile.no_civs_min": {"en": "No civs with {min}+ games.", "tr": "{min}+ maçı olan medeniyet yok."},
    "profile.full_rivalry_list": {"en": "Full Rivalry List", "tr": "Tüm Rakip Listesi"},
    "overview.high_elo_wins": {"en": "Wins vs Higher ELO", "tr": "Yüksek ELO Galibiyetleri"},
    "profile.matchups_difficult": {"en": "Most Difficult", "tr": "En Zorlu"},
    "profile.matchups_easiest": {"en": "Easiest", "tr": "En Kolay"},
    "overview.upsets_desc": {"en": "Most wins against statistically stronger opponents.", "tr": "İstatistiksel olarak daha güçlü rakiplere karşı en çok galibiyet."},
    "synergy.mode_title": {"en": "Calculation Mode", "tr": "Hesaplama Modu"},
    "synergy.mode_general": {"en": "General Synergy (Vs Others)", "tr": "Genel Sinerji (Başkalarına Karşı)"},
    "synergy.mode_internal": {"en": "Active Lobby (Internal)", "tr": "Aktif Lobi (Birbirimize Karşı)"},
    "admin.backfill_history": {"en": "Full History Backfill", "tr": "Tam Geçmiş Yükle (Backfill)"},
    "admin.backfill_info": {"en": "Fetches COMPLETE match history from aoe2insights.com (bypassing the 50-match limit). Matches are merged with existing database.", "tr": "aoe2insights.com üzerinden TÜM maç geçmişini çeker (50 maç limitini aşar). Maçlar mevcut veritabanı ile birleştirilir."},
    "admin.start_backfill": {"en": "Start Backfill Process", "tr": "Güncellemeyi Başlat"},
    "admin.fetching_history": {"en": "Fetching history for {player} ({current}/{total})...", "tr": "{player} geçmişi çekiliyor ({current}/{total})..."},
    "admin.fetched_processing": {"en": "Fetched {count} matches for {player}. Processing...", "tr": "{player} için {count} maç çekildi. İşleniyor..."},
    "admin.backfill_complete": {"en": "Backfill Complete! Total new matches inserted: {count}", "tr": "İşlem Tamamlandı! Toplam eklenen maç: {count}"},




}

def get_text(key: str, lang: str = DEFAULT_LANG) -> str:
    """Retrieve translated text."""
    # Fallback to key if not found, fallback to English if lang not found
    entry = TRANSLATIONS.get(key)
    if not entry:
        return f"[{key}]"
    
    return entry.get(lang, entry.get("en", f"[{key}]"))
