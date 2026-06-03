-- SifuFinds — Initial seed data
-- Run AFTER schema.sql in the Supabase SQL Editor.
-- This populates tips and news with the same data currently hardcoded in
-- assets/shared.js so the site has data immediately on first deploy.

-- ─────────────────────────────────────────────────────────────────────────────
-- TIPS
-- ─────────────────────────────────────────────────────────────────────────────
insert into tips (league, sport_key, match, pred, analysis, odds, via, conf, time_disp, date_label, is_ai, status, sort_order) values
('World Cup 2026 · Pre-Tournament Friendly','world','Nigeria vs USA','Over 2.5 Goals','Nigeria''s World Cup squad features Osimhen, Lookman and Chukwueze — a lethal attacking trio. The USA hosts the tournament and their high-press style opens matches up. Both teams are finalising squads and will attack freely.','1.75','Bet9ja',73,'20:00 UTC','Today',false,'active',1),
('World Cup 2026 · Pre-Tournament Friendly','world','Morocco vs Croatia','Morocco Win or Draw','Morocco are AFCON 2023 champions and Africa''s strongest World Cup contenders. Croatia face a transitional squad post-retirements. The Atlas Lions'' organised defence and pace on the break make them hard to beat.','1.65','1xBet',74,'17:00 UTC','Today',false,'active',2),
('CAF Champions League · Final','cafl','Mamelodi Sundowns vs Al Ahly','Over 2.5 Goals','The CAF CL Final brings together Africa''s two most dominant clubs. Sundowns'' fast transitions and Al Ahly''s clinical finishing make for a high-scoring encounter. Both sides scored in 8 of their last 9 CAF knockout matches.','1.85','Betway',72,'19:00 UTC','Today',false,'active',3),
('AFCON 2027 Qualifier','afcon','Nigeria vs Rwanda','Nigeria Win & Over 1.5','Super Eagles at home have won 11 of their last 12 qualifying games. Rwanda have conceded 2+ goals in 4 of their last 5 away qualifiers. With Osimhen leading the line, a commanding home win is expected.','1.65','Bet9ja',80,'16:00 UTC','Today',false,'active',4),
('AFCON 2027 Qualifier','afcon','Senegal vs DR Congo','Senegal Win','Senegal are the reigning AFCON champions and unbeaten in 9 home qualifiers. DR Congo are inconsistent away from home. Mané''s leadership and the Dakar crowd give the Lions of Teranga clear edge.','1.70','1xBet',76,'18:00 UTC','Today',false,'active',5),
('Kenya Premier League · Playoff','local','Gor Mahia vs AFC Leopards','Both Teams to Score','The Mashemeji Derby is Kenyan football''s fiercest rivalry. Both sides are in goalscoring form and this playoff encounter historically produces goals at both ends. 7 of the last 10 meetings saw BTTS.','1.75','Betika',70,'13:00 UTC','Today',false,'active',6),
('NPFL · Super 8','local','Enyimba FC vs Rivers United','Enyimba Win','Enyimba are Nigeria''s most decorated club. At home in Aba they have the crowd and momentum behind them. Rivers United have been inconsistent and conceded first in 4 of their last 5 away ties.','1.90','Bet9ja',67,'15:00 UTC','Today',false,'active',7),
('CAF Confederation Cup · Semi-Final','cafl','Étoile du Sahel vs Zamalek','Both Teams to Score','A tight second-leg semi-final. Étoile lead by a single goal. Zamalek must attack, opening space on the counter. Both sides have prolific attackers and goals look inevitable.','1.95','22Bet',64,'18:00 UTC','Tomorrow',false,'active',8),
('NBA Finals 2026 · Game 1','basketball','San Antonio Spurs vs New York Knicks','Spurs Win','The Spurs host Game 1 with home advantage at Frost Bank Center. Victor Wembanyama is a generational talent — 25 points, 11.5 rebounds and 3.1 blocks per game. The Knicks'' Jalen Brunson is dangerous but Wembanyama''s rim protection and scoring ability make San Antonio favourites at home.','1.54','1xBet',72,'00:30 UTC','Tomorrow',false,'active',9),
('NBA Finals 2026 · Game 1','basketball','San Antonio Spurs vs New York Knicks','Over 218.5 Points','Both teams are high-octane offences — SA averaged 119.8 PPG and NY averaged 116.5 PPG during the regular season. Expect a fast-paced Game 1 with plenty of scoring. The over has hit in 8 of their last 10 playoff meetings.','1.91','Bet9ja',68,'00:30 UTC','Tomorrow',false,'active',10),
('French Open 2026 · Women''s Final','tennis','Iga Świątek vs Madison Keys','Świątek Win','Świątek has won Roland Garros four times and looks imperious on clay again this year. Keys is dangerous with a big serve, but on slow red clay Świątek''s baseline consistency and mental strength are overwhelming.','1.55','Bet9ja',77,'12:00 UTC','In 4 days',false,'active',11),
('French Open 2026 · Men''s Final','tennis','Carlos Alcaraz vs Jannik Sinner','Alcaraz Win','Alcaraz is the defending Roland Garros champion and the dominant clay-court force this season. His footwork, variety and fighting spirit are unmatched. Sinner has improved on clay but has never reached a Roland Garros final before.','1.80','1xBet',70,'14:00 UTC','In 5 days',false,'active',12),
('SA vs India · Test Series','cricket','South Africa vs India','South Africa Win','The Proteas have their best Test side in a decade. Their pace trio of Rabada, Nortje and Jansen is the most feared attack in the world. India''s batting depth is immense but they''ve historically struggled against sustained world-class pace.','2.20','Hollywoodbets',60,'08:00 UTC','In 2 days',false,'active',13),
('Super Rugby Pacific 2026 · Final','rugby','Blues vs Brumbies','Blues Win','The Blues had the most dominant Super Rugby season in years with a 12-2 regular-phase record. Their backline — led by Beauden Barrett and Rieko Ioane — is the most dangerous in the competition.','1.75','1xBet',68,'09:05 UTC','In 2 days',false,'active',14),
('WBC Heavyweight Championship','boxing','Oleksandr Usyk vs Daniel Dubois 2','Usyk Win','Usyk is the most complete heavyweight of his generation — elite footwork, IQ and a chin tested at the highest level. In their first meeting Usyk''s movement and jab neutralised Dubois''s power entirely.','1.45','Bet9ja',80,'21:00 UTC','Tomorrow',false,'active',15);

-- ─────────────────────────────────────────────────────────────────────────────
-- NEWS
-- ─────────────────────────────────────────────────────────────────────────────
insert into news_items (cat, color, title, date_label, sort_order) values
('World Cup 2026','#E60000','World Cup 2026 Kicks Off June 11 – Best Odds for African Teams','Today',1),
('Nigeria','#00875A','Super Eagles Name Final 26-Man Squad for World Cup 2026','Yesterday',2),
('CAF','#C62828','CAF Champions League Final Preview – Sundowns vs Al Ahly','2 days ago',3),
('Morocco','#009A44','Morocco World Cup 2026 Odds – Atlas Lions Favourites in Their Group','3 days ago',4),
('Kenya','#007A4D','Betika Reaches 10 Million Users – New World Cup Features Added','4 days ago',5),
('Africa','#FF6B00','Mobile Money Betting Surges 45% as World Cup 2026 Approaches','5 days ago',6);
