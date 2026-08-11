// ── SITE URLS (overridden per-page via inline <script> before this file) ──────
// Each page defines: const SITE={home,tips,casino,odds,countries}
// v:20260605-1

// ── DATES ─────────────────────────────────────────────────────────────────────
const NOW=new Date();
const DATE_STR=NOW.toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric'});
const MON_YR=NOW.toLocaleDateString('en-GB',{month:'long',year:'numeric'});
const SHORT_DATE=NOW.toLocaleDateString('en-GB',{day:'numeric',month:'short'});

// ── PAYMENT COLORS ─────────────────────────────────────────────────────────────
const PM_C={'M-Pesa':'#4CAF50|#fff','M-Pesa (Vodacom)':'#4CAF50|#fff','M-Pesa DRC (Vodacom)':'#4CAF50|#fff','M-Pesa Mozambique':'#4CAF50|#fff','MTN MoMo':'#FFC107|#333','MTN MoMo Zambia':'#FFC107|#333','MTN MoMo Rwanda':'#FFC107|#333','Airtel Money':'#E60000|#fff','Airtel Money DRC':'#E60000|#fff','Airtel Money Rwanda':'#00BCD4|#fff','Airtel Money Zambia':'#E60000|#fff','Airtel Money Malawi':'#E60000|#fff','AirtelTigo Money':'#E60000|#fff','AirtelTigo':'#E60000|#fff','Orange Money':'#FF6B00|#fff','Orange Money Botswana':'#FF6B00|#fff','OPay':'#1565C0|#fff','PalmPay':'#00BCD4|#fff','Bank Transfer':'#607D8B|#fff','Visa':'#1A1F71|#fff','Mastercard':'#B0050A|#fff','USSD':'#5D4037|#fff','USSD *644#':'#5D4037|#fff','FNB':'#009E60|#fff','FNB Botswana':'#009E60|#fff','FNB Namibia':'#009E60|#fff','Standard Bank':'#0033A0|#fff','Standard Bank Namibia':'#0033A0|#fff','Nedbank':'#007A4D|#fff','Capitec':'#0070BA|#fff','Instant EFT':'#455A64|#fff','Blue Voucher':'#1565C0|#fff','Vodafone Cash':'#E60000|#fff','Equitel':'#7B1FA2|#fff','Tigo Pesa':'#1565C0|#fff','Halotel Pesa':'#E65100|#fff','Quickteller':'#E91E63|#fff','Wave':'#1FB5FF|#fff','EcoCash (Econet)':'#00853F|#fff','OneMoney (NetOne)':'#1a6b35|#fff','TNM Mpamba':'#0055A4|#fff','e-Mola':'#0055A4|#fff','Unitel Money':'#FF6B00|#fff','Africell Money':'#E60000|#fff','Bank Windhoek':'#003580|#fff','Zamtel Mobile Money':'#009A44|#fff','Betika USSD':'#007A4D|#fff','1Voucher':'#0D47A1|#fff','Ozow':'#6A1B9A|#fff','PayU':'#009688|#fff','FNB eWallet':'#009E60|#fff','Commercial Bank of Ethiopia':'#1a6b35|#fff','Halo (Somtel)':'#E65100|#fff','CIB Bank':'#003580|#fff','Ecocash':'#00853F|#fff'};

// ── LIVE-DATA CURRENCY GUARD ──────────────────────────────────────────────────
// Returns false when a live offer string contains a currency symbol that belongs
// to a different country, preventing Nigerian ₦ values from polluting Kenya,
// Ghana, etc. pages when bookmaker names match across countries.
function _liveTopFits(val,sym){
  if(!val||!sym)return true;
  const known=['₦','KSh','GH₵','TSh','USh','ZK','Br','CFA','RWF','MWK','MZN','AOA','CDF','BWP','NAD','EGP','MAD','Le'];
  for(const s of known){if(s!==sym&&val.includes(s))return false;}
  // R-prefix guard (ZA symbol='R'): "R25 Free Bet" must not reach other countries
  if(sym!=='R'&&/\bR\d/.test(val))return false;
  // $-prefix guard (ZW/LR symbol='$')
  if(sym!=='$'&&/\$\d/.test(val))return false;
  return true;
}

// ── COUNTRY EMOJI ──────────────────────────────────────────────────────────────
const CTY_EMOJI={NG:'🇳🇬',KE:'🇰🇪',GH:'🇬🇭',ZA:'🇿🇦',TZ:'🇹🇿',UG:'🇺🇬',ZM:'🇿🇲',ET:'🇪🇹',CI:'🇨🇮',CM:'🇨🇲',SN:'🇸🇳',RW:'🇷🇼',ZW:'🇿🇼',MW:'🇲🇼',MZ:'🇲🇿',AO:'🇦🇴',CD:'🇨🇩',BW:'🇧🇼',NA:'🇳🇦',EG:'🇪🇬',MA:'🇲🇦',SL:'🇸🇱',LR:'🇱🇷'};

// ── COUNTRY METADATA ───────────────────────────────────────────────────────────
const COUNTRY_DATA={
  NG:{name:'Nigeria',flag:'🇳🇬',currency:'NGN',symbol:'₦',region:'west',regulator:'NLRC (National Lottery Regulatory Commission)',about:'Nigeria is Africa\'s largest and most active sports betting market with over 60 million registered bettors. The market is regulated by the National Lottery Regulatory Commission (NLRC) with state-level oversight. Football dominates, particularly the Nigerian Premier Football League (NPFL), UEFA Champions League, and English Premier League.',payments:['OPay','PalmPay','Bank Transfer','Visa','Mastercard','USSD'],leagues:['NPFL','CAF Champions League','Premier League','UEFA Champions League','AFCON']},
  KE:{name:'Kenya',flag:'🇰🇪',currency:'KES',symbol:'KSh',region:'east',regulator:'BCLB (Betting Control and Licensing Board)',about:'Kenya has one of East Africa\'s most mature betting markets. The Betting Control and Licensing Board (BCLB) regulates all operators. M-Pesa is the dominant payment method. The Kenya Premier League (KPL) and SportPesa Premier League attract massive local betting interest.',payments:['M-Pesa','Airtel Money','Equitel','USSD *644#'],leagues:['Kenya Premier League','CAF Champions League','Premier League','AFCON','World Cup Qualifiers']},
  GH:{name:'Ghana',flag:'🇬🇭',currency:'GHS',symbol:'GH₵',region:'west',regulator:'GCA (Gaming Commission of Ghana)',about:'Ghana\'s betting industry is regulated by the Gaming Commission of Ghana (GCA). MTN MoMo and Vodafone Cash are the preferred deposit methods. The Ghana Premier League (GPL) sees significant local wagering activity alongside international competitions.',payments:['MTN MoMo','Vodafone Cash','AirtelTigo Money','Visa','Mastercard'],leagues:['Ghana Premier League','CAF Confederation Cup','Premier League','AFCON','World Cup Qualifiers']},
  ZA:{name:'South Africa',flag:'🇿🇦',currency:'ZAR',symbol:'R',region:'south',regulator:'WCGRB / NGB / ECGBB (Provincial Gambling Boards)',about:'South Africa has the continent\'s most regulated betting environment, overseen by provincial gambling boards including the WCGRB and NGB. FICA verification is required for all accounts. Local favourites include the PSL (DStv Premiership), Springboks rugby, and cricket.',payments:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard','Instant EFT','Blue Voucher'],leagues:['DStv Premiership','Springboks Rugby','Proteas Cricket','CAF Champions League','Premier League']},
  TZ:{name:'Tanzania',flag:'🇹🇿',currency:'TZS',symbol:'TSh',region:'east',regulator:'Gaming Board of Tanzania',about:'Tanzania\'s betting market is regulated by the Gaming Board of Tanzania. Mobile money via M-Pesa (Vodacom), Airtel Money, Tigo Pesa, and Halotel is the main payment route. The Tanzania Premier League and CAF competitions are the most wagered events.',payments:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Halotel Pesa','Bank Transfer'],leagues:['Tanzania Premier League','CAF Champions League','Premier League','AFCON']},
  UG:{name:'Uganda',flag:'🇺🇬',currency:'UGX',symbol:'USh',region:'east',regulator:'Uganda National Council for Sports (UNCS)',about:'Uganda\'s sports betting sector is regulated by the Uganda National Council for Sports. MTN MoMo and Airtel Money Uganda dominate payments. The Uganda Premier League and African competitions drive the most betting activity.',payments:['MTN MoMo','Airtel Money','Bank Transfer','Visa','Mastercard'],leagues:['Uganda Premier League','CAF Confederation Cup','Premier League','AFCON']},
  ZM:{name:'Zambia',flag:'🇿🇲',currency:'ZMW',symbol:'ZK',region:'south',regulator:'Gaming and Lotteries Board (GLB)',about:'Zambia\'s betting industry is supervised by the Gaming and Lotteries Board. MTN MoMo Zambia and Airtel Money Zambia are the main mobile payment channels. The FAZ Super Division and CAF competitions are the most popular betting markets.',payments:['MTN MoMo Zambia','Airtel Money Zambia','Zamtel Mobile Money','Bank Transfer','Visa'],leagues:['FAZ Super Division','CAF Champions League','Premier League','AFCON']},
  ET:{name:'Ethiopia',flag:'🇪🇹',currency:'ETB',symbol:'Br',region:'east',regulator:'National Lottery Administration (NLA)',about:'Note: Ethiopia\'s government revoked sports betting licences from all operators in 2024. The market is currently restricted. International operators may still accept Ethiopian players at their own discretion. Always verify local regulations before betting. The National Lottery Administration (NLA) oversees gambling.',payments:['Bank Transfer','Visa','Mastercard'],leagues:['Ethiopian Premier League','CAF Confederation Cup','Premier League','AFCON']},
  CI:{name:'Ivory Coast',flag:'🇨🇮',currency:'XOF',symbol:'CFA',region:'west',regulator:'ARJEL CI (Autorité de Régulation des Jeux en Ligne)',about:'Côte d\'Ivoire has a well-established betting market regulated by ARJEL. Orange Money and MTN MoMo are the primary mobile payment channels. International operators including 1xBet, Melbet and Premier Bet compete alongside local offerings. The Ligue 1 CI and CAF competitions drive the most wagering activity.',payments:['Orange Money','MTN MoMo','Wave','Bank Transfer','Visa'],leagues:['Ligue 1 CI','CAF Champions League','Ligue 1 France','Premier League','AFCON']},
  CM:{name:'Cameroon',flag:'🇨🇲',currency:'XAF',symbol:'CFA',region:'central',regulator:'Autorité des Marchés des Jeux (AMJ)',about:'Cameroon\'s betting market is growing rapidly. Orange Money and MTN MoMo are the dominant payments. The MTN Elite One (local top flight) and AFCON — which Cameroon hosted in 2022 — are the biggest betting events.',payments:['Orange Money','MTN MoMo','Bank Transfer','Visa','Mastercard'],leagues:['MTN Elite One','CAF Champions League','Ligue 1 France','Premier League','AFCON']},
  SN:{name:'Senegal',flag:'🇸🇳',currency:'XOF',symbol:'CFA',region:'west',regulator:'Autorité de Régulation des Télécommunications et des Postes (ARTP)',about:'Senegal\'s betting scene is growing quickly, driven by mobile money and a passionate football culture following AFCON 2022 glory. Wave and Orange Money are the main payment methods. The Ligue 1 Sénégal and European leagues attract most bettors.',payments:['Orange Money','Wave','MTN MoMo','Bank Transfer','Visa'],leagues:['Ligue 1 Sénégal','CAF Champions League','Ligue 1 France','Premier League','AFCON']},
  RW:{name:'Rwanda',flag:'🇷🇼',currency:'RWF',symbol:'RWF',region:'east',regulator:'Rwanda Gaming Commission (RGC)',about:'Rwanda has a strictly regulated gaming environment overseen by the Rwanda Gaming Commission. MTN MoMo Rwanda and Airtel Money Rwanda are the primary payments. The Rwanda Premier League and East African club competitions drive local betting.',payments:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer','Visa'],leagues:['Rwanda Premier League','CAF Confederation Cup','Premier League','AFCON']},
  ZW:{name:'Zimbabwe',flag:'🇿🇼',currency:'USD',symbol:'$',region:'south',regulator:'Lotteries and Gaming Board of Zimbabwe',about:'Zimbabwe operates a USD-denominated betting market regulated by the Lotteries and Gaming Board. EcoCash (Econet) is the dominant mobile payment. The Zimbabwe Premier Soccer League (PSL) and regional African competitions are the most popular markets.',payments:['EcoCash (Econet)','OneMoney (NetOne)','Bank Transfer','Visa','Mastercard'],leagues:['Zimbabwe Premier Soccer League','CAF Champions League','Premier League','AFCON']},
  MW:{name:'Malawi',flag:'🇲🇼',currency:'MWK',symbol:'MWK',region:'south',regulator:'Malawi Gaming Board',about:'Malawi\'s betting market is regulated by the Malawi Gaming Board. Airtel Money Malawi and TNM Mpamba are the main mobile payment options. The Super League of Malawi and regional competitions attract local bettors.',payments:['Airtel Money Malawi','TNM Mpamba','Bank Transfer','Visa'],leagues:['Super League of Malawi','CAF Confederation Cup','Premier League','AFCON']},
  MZ:{name:'Mozambique',flag:'🇲🇿',currency:'MZN',symbol:'MZN',region:'south',regulator:'Instituto para a Gestão das Apostas (IGA)',about:'Mozambique\'s regulated betting market is overseen by the IGA. M-Pesa Mozambique (Vodacom) is the leading payment method. Hollywoodbets has a strong retail presence alongside digital operators. The Moçambola and CAF events dominate wagering.',payments:['M-Pesa Mozambique','e-Mola','Bank Transfer','Visa'],leagues:['Moçambola','CAF Champions League','Premier League','AFCON']},
  AO:{name:'Angola',flag:'🇦🇴',currency:'AOA',symbol:'AOA',region:'central',regulator:'Instituto do Desporto (ID Angola)',about:'Angola is an emerging betting market with growing smartphone penetration. Unitel Money and bank transfers are the main payment channels. The GiraBola (local top flight) and Portuguese Liga NOS attract most bettors.',payments:['Unitel Money','Bank Transfer','Visa','Mastercard'],leagues:['GiraBola','CAF Confederation Cup','Primeira Liga Portugal','Premier League']},
  CD:{name:'DR Congo',flag:'🇨🇩',currency:'CDF',symbol:'CDF',region:'central',regulator:'Autorité de Régulation des Jeux (ARJ)',about:'The DRC is one of Africa\'s largest potential betting markets. M-Pesa DRC, Airtel Money DRC, and Orange Money serve mobile payments. The Linafoot (local top flight) and AFCON draw the most betting interest.',payments:['M-Pesa DRC (Vodacom)','Airtel Money DRC','Orange Money','Bank Transfer'],leagues:['Linafoot','CAF Champions League','Premier League','AFCON']},
  BW:{name:'Botswana',flag:'🇧🇼',currency:'BWP',symbol:'BWP',region:'south',regulator:'Gambling Authority of Botswana',about:'Botswana has a well-regulated betting market overseen by the Gambling Authority. FNB Botswana and Orange Money Botswana are the main payment channels. The Botswana Premier League and South African PSL attract most bettors.',payments:['FNB Botswana','Orange Money Botswana','Bank Transfer','Visa','Mastercard'],leagues:['Botswana Premier League','CAF Confederation Cup','DStv Premiership','Premier League']},
  NA:{name:'Namibia',flag:'🇳🇦',currency:'NAD',symbol:'NAD',region:'south',regulator:'Gambling Board of Namibia',about:'Namibia\'s betting market mirrors South Africa, sharing currency parity with the ZAR. The Gambling Board of Namibia regulates operators. FNB Namibia and Standard Bank Namibia dominate banking. The NFA Premier League and South African PSL are popular.',payments:['FNB Namibia','Standard Bank Namibia','Bank Windhoek','Bank Transfer','Visa'],leagues:['NFA Premier League','CAF Confederation Cup','DStv Premiership','Premier League']},
  EG:{name:'Egypt',flag:'🇪🇬',currency:'EGP',symbol:'EGP',region:'north',regulator:'Egyptian Gambling Regulatory Authority (EGRA)',about:'Egypt is one of Africa\'s largest sports betting markets with a passionate football culture. The Egyptian Premier League is among Africa\'s strongest domestic competitions. International bookmakers accept Egyptian bettors and the market is growing rapidly with mobile penetration. Vodafone Cash Egypt and bank transfer are the main payment routes.',payments:['Vodafone Cash Egypt','Orange Money Egypt','Bank Transfer','Visa','Mastercard'],leagues:['Egyptian Premier League','CAF Champions League','Premier League','La Liga','World Cup 2026']},
  MA:{name:'Morocco',flag:'🇲🇦',currency:'MAD',symbol:'MAD',region:'north',regulator:'MDJS (Marocaine des Jeux et des Sports)',about:'Morocco has a regulated gambling market overseen by MDJS. PMU Maroc (Pari Mutuel Urbain) is the state-licensed operator. International bookmakers also serve Moroccan bettors. Morocco\'s 2022 World Cup semi-final run ignited massive betting interest. The Botola Pro is the top domestic league and La Liga, Serie A and Champions League draw huge volumes.',payments:['Bank Transfer','CIH Bank','Attijari Bank','Orange Money Morocco','Visa','Mastercard'],leagues:['Botola Pro','CAF Champions League','Premier League','La Liga','World Cup 2026']},
  SL:{name:'Sierra Leone',flag:'🇸🇱',currency:'SLL',symbol:'Le',region:'west',regulator:'National Lotteries Authority (NLA)',about:'Sierra Leone has a growing sports betting market regulated by the National Lotteries Authority. Orange Money Sierra Leone and Africell Money are the main mobile payment channels. The Sierra Leone Premier League and AFCON attract the most betting interest.',payments:['Orange Money Sierra Leone','Africell Money','Bank Transfer','Visa'],leagues:['Sierra Leone Premier League','CAF Confederation Cup','Premier League','AFCON']},
  LR:{name:'Liberia',flag:'🇱🇷',currency:'LRD',symbol:'$',region:'west',regulator:'National Lottery of Liberia',about:'Liberia has an emerging sports betting market. The National Lottery of Liberia oversees gambling activities. Lonestar Cell MTN Mobile Money and Orange Liberia are the main mobile payment options. Football is the dominant sport with the LFA League and AFCON drawing most interest.',payments:['Lonestar MTN Mobile Money','Orange Liberia','Bank Transfer','Visa'],leagues:['LFA League','CAF Confederation Cup','Premier League','AFCON']}
};

// ── AFFILIATE FILTER ──────────────────────────────────────────────────────────
// Keep in sync with CLAUDE.md's "Brands With a Real Affiliate Link" tracking-domain
// list — this was missing 3 of the 9 documented domains until 2026-08-08.
const AFFILIATE_DOMAINS=['reffpa.com','refpa3665.com','bwredir.com','combodef.com','1212fghnna.com','trackrt.tictacbets.co.za','goaffnk.com','track.trkbxa.click','track.bettapartners.co.za','fairpaff.top'];
function isAffiliate(b){return AFFILIATE_DOMAINS.some(d=>b.url&&b.url.includes(d));}
function affiliateBooks(books){return(books||[]).filter(isAffiliate);}

// ── BOOKS DATA ─────────────────────────────────────────────────────────────────
const BOOKS={
NG:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Nigeria',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Welcome Bonus in Nigeria',off:'300% First Deposit Bonus – Up to ₦1,200,000',top:'₦1,200,000',stars:4,min:'₦100',instant:true,cashout:true,stream:true,sports:50,lic:'NLRC Licensed',nodep:false,badge:'hot',terms:'Code 1BONUSNG. 300% on first deposit up to ₦1,200,000. Wager x5 accumulators at min odds 1.40. 30 days. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard','MTN MoMo']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Nigeria',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to ₦480,000',top:'₦480,000',stars:4,min:'₦100',instant:true,cashout:false,stream:true,sports:150,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to ₦480,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard','MTN MoMo']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Nigeria',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – Easy 5x Wagering',off:'200% First Deposit Bonus – Up to ₦130,000',top:'₦130,000',stars:3,min:'₦400',instant:false,cashout:true,stream:true,sports:40,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% up to ₦130,000. Wager x5 accumulators at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard','MTN MoMo','OPay']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Nigeria',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:57,lic:'NLRC Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard','MTN MoMo']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Nigeria',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to ₦200,000',top:'₦200,000',stars:4,min:'₦100',instant:true,cashout:true,stream:true,sports:50,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'200% match on first deposit up to ₦200,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard']},
{abbr:'B9',bg:'#00875A',tc:'#fff',name:'Bet9ja',url:'https://www.bet9ja.com',tag:"Nigeria's No.1 Licensed Bookmaker",off:'Get ₦2,500 Free Bet on Signup + 170% ACCA Boost',top:'₦2,500 Free',stars:5,min:'₦100',instant:true,cashout:true,stream:true,sports:30,lic:'NLRC Licensed',nodep:false,badge:'hot',terms:'Register with code 9BONUS. ₦2,500 free bet after verification. ACCA Boost up to 170% on 3+ leg multi-bets. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard','USSD']},
{abbr:'SB',bg:'#E71D29',tc:'#fff',name:'Sportybet Nigeria',url:'https://www.sportybet.com/ng/',tag:"Africa's Most Downloaded Betting App",off:'150% Welcome Bonus – Up to ₦30,000 Free Bet',top:'₦30,000',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:30,lic:'NLRC Licensed',nodep:false,badge:'hot',terms:'Min deposit ₦100. 150% as Free Bet Gifts on betslips with min odds 3.15. 7-day expiry. T&Cs. 18+.',pms:['OPay','Quickteller','Bank Transfer','Visa','Mastercard']},
{abbr:'BK',bg:'#001041',tc:'#fff',name:'BetKing',url:'https://www.betking.com',tag:'No Deposit – KingMakers-Backed Nigerian Brand',off:'₦100 Free Bets + 10 Aviator Flights – No Deposit',top:'₦100 No Deposit',stars:5,min:'₦0',instant:true,cashout:true,stream:true,sports:25,lic:'NLRC Licensed',nodep:true,badge:'new',terms:'Code BONUSKG. No deposit needed. ₦50 sportsbook + ₦50 virtual free bets + 10 Aviator flights credited next working day. 7-day expiry. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard','USSD']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Nigeria',url:'https://www.betway.com/en-ng/',tag:'International Brand – Fast Payouts',off:'Up to ₦100,000 in Free Bets – First 7 Days',top:'₦100,000',stars:4,min:'₦1,000',instant:true,cashout:true,stream:true,sports:28,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Code WAYBON. 10% of settled stakes up to ₦100,000/day for first 7 days. Min daily stake ₦1,000. Min odds 1.50. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Nigeria',url:'https://22bet.com',tag:'100% Bonus – Reliable Payouts',off:'100% First Deposit Bonus – Up to ₦207,500',top:'₦207,500',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:35,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Code BNSNG. 100% match up to ₦207,500. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard','MTN MoMo']},
{abbr:'MZ',bg:'#FFCB37',tc:'#1A1A2E',name:'MozzartBet Nigeria',url:'https://www.mozzartbet.com/en/',tag:'100% Bonus + 500 Aviator Free Bets',off:'100% Bonus Up to ₦50,000 + 500 Aviator Bets',top:'₦50,000',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'Deposit and get 100% match up to ₦50,000 + 500 Aviator free bets. Wagering requirements apply. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'NB',bg:'#1B5E20',tc:'#fff',name:'NairaBet',url:'https://www.nairabet.com',tag:"Nigeria's Pioneer Bookmaker – Est. 2009",off:'Free Bet on First Deposit + Daily Free Bets',top:'Free Bets',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:25,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Register and deposit to claim welcome free bet. Daily free bets for active players. T&Cs apply. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard']},
{abbr:'BB',bg:'#FFE60F',tc:'#1C1E24',name:'Bangbet Nigeria',url:'https://www.bangbet.com',tag:'Low Minimum Stake – Great for Beginners',off:'Deposit ₦50, Get ₦200 in Free Bets',top:'₦200 Free',stars:3,min:'₦50',instant:true,cashout:false,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Deposit ₦50 minimum and receive ₦200 in free bets. 7-day expiry. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'MS',bg:'#FFCA27',tc:'#111',name:'MSport Nigeria',url:'https://www.msport.com',tag:'200% Bonus – Fast Growing in West Africa',off:'200% Welcome Bonus – Up to ₦50,000',top:'₦50,000',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'',terms:'200% on first deposit up to ₦50,000. Wagering requirements apply. 14 days. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'Betpawa Nigeria',url:'https://www.betpawa.ng',tag:'Bet from ₦50 on Jackpots',off:'Weekly Jackpot – Win Millions from ₦50 Stake',top:'Jackpot from ₦50',stars:4,min:'₦50',instant:true,cashout:false,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'Bet from ₦50 on jackpot products. Weekly jackpot prizes available. OPay and MTN MoMo accepted. T&Cs. 18+.',pms:['OPay','MTN MoMo','Bank Transfer','Visa']},
{abbr:'SB247',bg:'#006400',tc:'#fff',name:'Surebet247',url:'https://www.surebet247.com',tag:'Nigerian Pioneer – Est. 2014',off:'100% Welcome Bonus',top:'100% Match',stars:4,min:'₦100',instant:true,cashout:true,stream:false,sports:25,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. OPay and PalmPay. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard']},
{abbr:'LSB',bg:'#0033A0',tc:'#fff',name:'LivescoreBet Nigeria',url:'https://www.livescorebet.com',tag:'Real-Time Odds Powered by Livescore',off:'100% First Deposit Bonus – Up to ₦50,000',top:'₦50,000',stars:4,min:'₦100',instant:true,cashout:true,stream:true,sports:30,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match up to ₦50,000. Wagering requirements apply. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'1W',bg:'#0D52FF',tc:'#fff',name:'1Win Nigeria',url:'https://1win.xyz',tag:'Casino + Sports in One App',off:'500% Welcome Package – Up to ₦500,000',top:'₦500,000',stars:3,min:'₦300',instant:true,cashout:true,stream:false,sports:40,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'500% package across first 4 deposits. Wagering x3. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard','OPay']},
{abbr:'ACB',bg:'#CC0000',tc:'#fff',name:'Accessbet',url:'https://www.accessbet.com.ng',tag:'NLRC Licensed – Instant OPay Withdrawals',off:'100% Welcome Bonus on First Deposit',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. OPay instant. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'N1B',bg:'#111111',tc:'#FFD700',name:'N1Bet Nigeria',url:'https://n1bet.ng',tag:'500+ Pre-Match Markets Daily',off:'100% Bonus Up to ₦50,000',top:'₦50,000',stars:3,min:'₦200',instant:true,cashout:true,stream:false,sports:35,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match up to ₦50,000. Wager x5. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'WZB',bg:'#7B1FA2',tc:'#fff',name:'Wazobet',url:'https://www.wazobet.com',tag:'Fast Payouts – NPFL & EPL',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. OPay accepted. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'BTA',bg:'#FF3C01',tc:'#fff',name:'Betano Nigeria',url:'https://www.betano.com/en-ng/',tag:'Kaizen Gaming – Growing Fast',off:'100% First Deposit Bonus – Up to ₦50,000',top:'₦50,000',stars:4,min:'₦500',instant:true,cashout:true,stream:true,sports:30,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'100% match up to ₦50,000. Wagering apply. T&Cs. 18+.',pms:['OPay','PalmPay','Bank Transfer','Visa','Mastercard']},
{abbr:'WGB',bg:'#E65100',tc:'#fff',name:'WinnerGoldenbet',url:'https://www.winnergoldenbet.com',tag:'Trusted Nigerian Bookmaker',off:'Welcome Bonus on First Deposit',top:'Bonus',stars:3,min:'₦100',instant:true,cashout:false,stream:false,sports:18,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Welcome bonus on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'YSP',bg:'#00695C',tc:'#fff',name:'YangaSport',url:'https://www.yangasport.com',tag:'Nigerian Sports Betting Platform',off:'100% Welcome Bonus on Signup',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'GB7',bg:'#1B5E20',tc:'#fff',name:'Gobet247',url:'https://www.gobet247.com',tag:'247 Betting – NPFL Coverage',off:'Welcome Bonus on First Deposit',top:'Bonus',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Welcome bonus on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'HLN',bg:'#430084',tc:'#fff',name:'Helabet Nigeria',url:'https://www.helabet.com',tag:'100+ Live Markets Daily',off:'100% Welcome Bonus Up to ₦25,000',top:'₦25,000',stars:3,min:'₦200',instant:true,cashout:true,stream:false,sports:25,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match up to ₦25,000. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'SKN',bg:'#00838F',tc:'#fff',name:'Sokabet Nigeria',url:'https://www.sokabet.com',tag:'Fast Withdrawals – OPay Instant',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:20,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'PPL',bg:'#0288D1',tc:'#fff',name:'Paripulse',url:'https://www.paripulse.com',tag:'50+ Sports Markets – New in Nigeria',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'₦200',instant:true,cashout:true,stream:false,sports:50,lic:'NLRC Licensed',nodep:false,badge:'new',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'BCN',bg:'#F57F17',tc:'#111',name:'BC.Game Nigeria',url:'https://bc.game',tag:'Crypto + Fiat – Casino & Sports',off:'Welcome Package Up to ₦500,000',top:'₦500,000',stars:3,min:'₦200',instant:true,cashout:true,stream:false,sports:30,lic:'NLRC Licensed',nodep:false,badge:'',terms:'Welcome package on first deposits. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','USDT']},
{abbr:'WDB',bg:'#4A148C',tc:'#fff',name:'Waddibet',url:'https://www.waddibet.com',tag:'Nigerian Brand – EPL & NPFL',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'88Z',bg:'#9C27B0',tc:'#fff',name:'888Starz Nigeria',url:'https://888starz.bet',tag:'Casino & Sports – International',off:'200% Welcome Package',top:'200% Bonus',stars:3,min:'₦500',instant:true,cashout:true,stream:false,sports:40,lic:'NLRC Licensed',nodep:false,badge:'',terms:'200% welcome package. Wagering apply. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard','OPay']},
{abbr:'PRB',bg:'#2E7D32',tc:'#fff',name:'Prosperbet',url:'https://www.prosperbet.ng',tag:'Prosper with Every Bet',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:18,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. OPay. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'BTF',bg:'#5D4037',tc:'#fff',name:'Betfarm',url:'https://www.betfarm.com.ng',tag:'Farm Your Winnings – NPFL Expert',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']},
{abbr:'BTL',bg:'#0D47A1',tc:'#fff',name:'Betonly Nigeria',url:'https://betonly.com',tag:'Bet Only the Best Odds',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'₦200',instant:true,cashout:true,stream:false,sports:25,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa','Mastercard']},
{abbr:'BBB',bg:'#F9A825',tc:'#111',name:'Betbaba',url:'https://www.betbaba.com.ng',tag:'Baba of Nigerian Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'₦100',instant:true,cashout:true,stream:false,sports:15,lic:'NLRC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['OPay','Bank Transfer','Visa']}
],
KE:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Kenya',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Highest in Kenya',off:'200% First Deposit Bonus – Up to KSh 20,000',top:'KSh 20,000',stars:4,min:'KSh 50',instant:true,cashout:true,stream:true,sports:50,lic:'BCLB Licensed',nodep:false,badge:'',terms:'200% match up to KSh 20,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Kenya',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:"300% Bonus – Kenya's Best Value",off:'300% First Deposit Bonus – Up to KSh 1,500',top:'KSh 1,500',stars:4,min:'KSh 50',instant:true,cashout:false,stream:true,sports:150,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Code MBMAX. 300% match up to KSh 1,500. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'Betwinner Kenya',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to KSh 16,250',top:'KSh 16,250',stars:3,min:'KSh 50',instant:true,cashout:true,stream:true,sports:40,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to KSh 16,250. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Kenya',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'KSh 50',instant:true,cashout:true,stream:false,sports:57,lic:'BCLB Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'HB',bg:'#430084',tc:'#fff',name:'HelaBet Kenya',url:'https://1212fghnna.com/L?tag=d_2204817m_52235c_&site=2204817&ad=52235',tag:'Licensed Kenyan Brand – Instant M-Pesa Payouts',off:'100% Welcome Bonus – Up to KSh 5,000',top:'KSh 5,000',stars:4,min:'KSh 10',instant:true,cashout:true,stream:false,sports:25,lic:'BCLB Licensed',nodep:false,badge:'new',terms:'100% match on first deposit up to KSh 5,000. M-Pesa instant. Wagering requirements apply. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Kenya',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to KSh 20,000',top:'KSh 20,000',stars:4,min:'KSh 50',instant:true,cashout:true,stream:true,sports:50,lic:'BCLB Licensed',nodep:false,badge:'new',terms:'200% match on first deposit up to KSh 20,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'BT',bg:'#FCED0E',tc:'#1B3A7A',name:'Betika Kenya',url:'https://www.betika.com/en-ke/',tag:"Operator of the Year 2025 – 8M+ Users",off:'Free Bet Gifts + Aviator Free Bets on Signup',top:'Free Bets',stars:5,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Lic. BK0000679',nodep:true,badge:'hot',terms:'Register and verify. Free bet on signup. Regular Aviator drops (KSh 30–500). M-Pesa via USSD *644#. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Equitel','USSD *644#']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Kenya',url:'https://www.sportpesa.co.ke',tag:'Official Sponsor of the SportPesa Premier League',off:'300% Welcome Karibu Gift on First Deposit',top:'300% Karibu',stars:5,min:'KSh 10',instant:true,cashout:true,stream:true,sports:30,lic:'BCLB Licensed',nodep:false,badge:'hot',terms:'Deposit and receive 300% Karibu Gift as free bets. M-Pesa instant. Jackpot products available. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer','Visa','Mastercard']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Kenya',url:'https://www.betway.com/en-ke/',tag:'M-Pesa Instant – Super Group East Africa',off:'50% Welcome Bonus – Up to KSh 5,000',top:'KSh 5,000',stars:4,min:'KSh 10',instant:true,cashout:true,stream:true,sports:28,lic:'BCLB Licensed',nodep:false,badge:'',terms:'50% match up to KSh 5,000. M-Pesa paybill: 880185. Wager 3x at odds 3.0+. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'OD',bg:'#3CC71B',tc:'#111',name:'Odibets Kenya',url:'https://odibets.com/',tag:'Low Stakes – Bet from Just KSh 10',off:'KSh 30 Free Bet on Registration',top:'KSh 30 Free',stars:4,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:true,badge:'',terms:'Register and verify. KSh 30 free bet instantly. M-Pesa and Airtel Money. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'MZ',bg:'#FFCB37',tc:'#1A1A2E',name:'MozzartBet Kenya',url:'https://www.mozzartbet.co.ke/',tag:'Live Streaming + Sports + Casino',off:'100% Welcome Bonus – Up to KSh 50,000',top:'KSh 50,000',stars:4,min:'KSh 50',instant:true,cashout:true,stream:true,sports:25,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 50,000 + Aviator free bets. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Kenya',url:'https://22bet.com',tag:'100% Bonus – KPL & EPL Coverage',off:'100% First Deposit Bonus – Up to KSh 19,000',top:'KSh 19,000',stars:4,min:'KSh 100',instant:true,cashout:true,stream:false,sports:35,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 19,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Visa','Mastercard']},
{abbr:'BG',bg:'#FFE60F',tc:'#1C1E24',name:'Bangbet Kenya',url:'https://www.bangbet.com',tag:'Low Minimum – Popular in Kenya & Nigeria',off:'Deposit KSh 10, Get KSh 50 Free Bet',top:'KSh 50 Free',stars:3,min:'KSh 10',instant:true,cashout:false,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Deposit KSh 10 to get KSh 50 in free bets. M-Pesa accepted. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'SB2',bg:'#E71D29',tc:'#fff',name:'Sportybet Kenya',url:'https://www.sportybet.com/ke/',tag:"Africa's #1 App – Now in Kenya",off:'150% Welcome Bonus Free Bet Gifts',top:'150% Match',stars:4,min:'KSh 10',instant:true,cashout:true,stream:false,sports:30,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Min deposit KSh 10. 150% as Free Bet Gifts. Min odds 3.15. 7-day expiry. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'CAP',bg:'#006400',tc:'#fff',name:'Captainsbet',url:'https://www.captainsbet.co.ke',tag:'Licensed Kenyan Brand – Quick M-Pesa',off:'100% Welcome Bonus – Up to KSh 5,000',top:'KSh 5,000',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 5,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'CZC',bg:'#00695C',tc:'#fff',name:'Chezacash',url:'https://www.chezacash.com',tag:'Kenyan Local Brand – KPL Coverage',off:'Free Bet on Registration',top:'Free Bet',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:true,badge:'',terms:'Free bet on registration. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'KWK',bg:'#1A237E',tc:'#fff',name:'Kwikbet',url:'https://www.kwikbet.co.ke',tag:'Instant Withdrawals – KPL Expert',off:'100% Welcome Bonus – Up to KSh 3,000',top:'KSh 3,000',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 3,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'MYB',bg:'#FF6F00',tc:'#fff',name:'Maybets',url:'https://www.maybets.com',tag:'Maybe Today – KPL & EPL Markets',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'SHB',bg:'#4CAF50',tc:'#fff',name:'Shabiki',url:'https://www.shabiki.com',tag:"Kenya's Home of Jackpots",off:'Jackpot – Win Millions Weekly',top:'Jackpot',stars:4,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Bet on jackpot products. M-Pesa *644#. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','USSD *644#']},
{abbr:'TCZ',bg:'#880E4F',tc:'#fff',name:'Tucheze',url:'https://www.tucheze.com',tag:'Bet Like a Champion',off:'100% Welcome Bonus – Up to KSh 5,000',top:'KSh 5,000',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 5,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'KLB',bg:'#0D47A1',tc:'#fff',name:'Kilibet',url:'https://www.kilibet.co.ke',tag:'Kilimanjaro Odds – EPL & KPL',off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'HAK',bg:'#33691E',tc:'#fff',name:'Hakibets',url:'https://www.hakibets.co.ke',tag:'Haki Odds – Kenyan Sports Specialist',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'LGB',bg:'#006064',tc:'#fff',name:'Ligibet',url:'https://www.ligibet.co.ke',tag:'League Specialist – KPL & EPL',off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'GNB',bg:'#4E342E',tc:'#fff',name:'Geniusbet',url:'https://www.geniusbet.co.ke',tag:'Genius Odds – 500+ Events Daily',off:'100% Welcome Bonus – Up to KSh 5,000',top:'KSh 5,000',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 5,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'MSB',bg:'#37474F',tc:'#fff',name:'Mossbets',url:'https://www.mossbets.com',tag:'Reliable Kenyan Bookmaker',off:'100% Welcome Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'QBT',bg:'#1565C0',tc:'#fff',name:'QBet',url:'https://www.qbet.co.ke',tag:'Quality Bets – KPL Focus',off:'Free Bet on Signup',top:'Free Bet',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:true,badge:'',terms:'Free bet on registration. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'PPT',bg:'#6A1B9A',tc:'#fff',name:'Pepeta',url:'https://www.pepeta.co.ke',tag:'Win Big Everyday',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'SFB',bg:'#2E7D32',tc:'#fff',name:'Sofabets',url:'https://www.sofabets.com',tag:'Sofa & Bet – Live Markets',off:'100% Welcome Bonus – Up to KSh 3,000',top:'KSh 3,000',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match up to KSh 3,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'PLM',bg:'#00796B',tc:'#fff',name:'Palmsbet',url:'https://www.palmsbet.co.ke',tag:'Palm Tree Odds – Kenyan Market',off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'MYO',bg:'#558B2F',tc:'#fff',name:'Moyobet',url:'https://www.moyobet.co.ke',tag:'Heart of Kenyan Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'PKK',bg:'#E65100',tc:'#fff',name:'Pakakumi',url:'https://www.pakakumi.com',tag:'Win Big – KPL Jackpots',off:'Jackpot from KSh 10',top:'Jackpot',stars:4,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'hot',terms:'Bet from KSh 10 on jackpots. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','USSD *644#']},
{abbr:'JMB',bg:'#0288D1',tc:'#fff',name:'Jambobet',url:'https://www.jambobet.co.ke',tag:"Jambo! – Kenya's Fun Betting",off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'VVB',bg:'#C62828',tc:'#fff',name:'Vivabet',url:'https://www.vivabet.co.ke',tag:'Viva Betting – Live & Pre-Match',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'JNT',bg:'#4527A0',tc:'#fff',name:'Jantabets',url:'https://www.jantabets.co.ke',tag:'Janta – Bet & Win in Kenya',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'WZT',bg:'#4527A0',tc:'#fff',name:'Wezabet',url:'https://www.wezabet.com',tag:'Weza – Bet & Win',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'TGB',bg:'#00838F',tc:'#fff',name:'Tigonbet',url:'https://www.tigonbet.co.ke',tag:'Tigon Odds – Fast & Reliable',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'GMN',bg:'#1A237E',tc:'#FFD700',name:'Gamemania',url:'https://www.gamemania.co.ke',tag:'Casino & Sports – All-in-One',off:'100% Welcome Bonus + Casino Spins',top:'100% + Spins',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match + free spins. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money','Bank Transfer']},
{abbr:'KSB',bg:'#388E3C',tc:'#fff',name:'Kessbet',url:'https://www.kessbet.com',tag:'Kenyan Sports Specialist',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BWN',bg:'#0056A2',tc:'#fff',name:'Betwin',url:'https://www.betwin.co.ke',tag:'Win Every Day – KPL Markets',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'P90',bg:'#1B5E20',tc:'#fff',name:'Pitch90Bet',url:'https://www.pitch90bet.com',tag:'Football Only – Expert KPL Odds',off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:10,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Football specialist. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BCK',bg:'#F57F17',tc:'#111',name:'BC.Game Kenya',url:'https://bc.game',tag:'Crypto Betting – AFCON & EPL',off:'Welcome Package Up to KSh 200,000',top:'KSh 200,000',stars:3,min:'KSh 100',instant:true,cashout:true,stream:false,sports:30,lic:'BCLB Licensed',nodep:false,badge:'',terms:'Welcome package across first deposits. Crypto and M-Pesa. T&Cs. 18+.',pms:['M-Pesa','USDT','Bank Transfer']},
{abbr:'BGK',bg:'#BF360C',tc:'#fff',name:'BetGr8 Kenya',url:'https://www.betgr8.co.ke',tag:'Gr8 Odds – KPL & Champions League',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BNB',bg:'#283593',tc:'#fff',name:'Bandabets',url:'https://www.bandabets.com',tag:"Kenya's Community Betting Platform",off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'CRK',bg:'#D50000',tc:'#fff',name:'CrashKali',url:'https://www.crashkali.com',tag:'Crash Game Specialist – Aviator & More',off:'100% Bonus + Crash Free Plays',top:'100% + Plays',stars:3,min:'KSh 20',instant:true,cashout:true,stream:false,sports:10,lic:'BCLB Licensed',nodep:false,badge:'new',terms:'100% match + crash free plays. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'HOT',bg:'#FF6D00',tc:'#fff',name:'HotCrash',url:'https://www.hotcrash.co.ke',tag:'Hot Crash Games – Win in Seconds',off:'100% Welcome Bonus + Crash Plays',top:'100% + Plays',stars:3,min:'KSh 20',instant:true,cashout:true,stream:false,sports:10,lic:'BCLB Licensed',nodep:false,badge:'new',terms:'100% match + crash free plays. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BFM',bg:'#AD1457',tc:'#fff',name:'BetFalme',url:'https://www.betfalme.com',tag:'Falme – Kenyan Local Brand',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BKM',bg:'#004D40',tc:'#fff',name:'BetKumi',url:'https://www.betkumi.com',tag:'Kumi Odds – 10 Reasons to Bet Here',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'PLY',bg:'#1A237E',tc:'#fff',name:'Playmaster',url:'https://www.playmaster.co.ke',tag:'Master the Game – KPL & EPL',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:20,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'SKT',bg:'#6D4C41',tc:'#fff',name:'Sakatabets',url:'https://www.sakatabets.com',tag:'Sakata – Dance & Win in Kenya',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'BBU',bg:'#FFE60F',tc:'#1C1E24',name:'BetBureau',url:'https://www.betbureau.co.ke',tag:'Bureau of Best Odds in Kenya',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'PKM',bg:'#5D4037',tc:'#fff',name:'Pakamia',url:'https://www.pakamia.com',tag:'Bet Smart in Kenya',off:'Free Bet on Registration',top:'Free Bet',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Licensed',nodep:true,badge:'',terms:'Free bet on registration. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']},
{abbr:'9UB',bg:'#F57F17',tc:'#fff',name:'9UBet',url:'https://www.9ubet.co.ke',tag:'9 in 1 – Multi-Sport Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'KSh 10',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','Airtel Money']}
],
GH:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Ghana',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – HD Live Streaming',off:'200% First Deposit Bonus – Up to GH₵2,846',top:'GH₵2,846',stars:4,min:'GH₵5',instant:true,cashout:true,stream:true,sports:50,lic:'GCA Licensed',nodep:false,badge:'',terms:'200% match up to GH₵2,846. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Ghana',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:"300% Bonus – Ghana's Highest Offer",off:'300% First Deposit Bonus – Up to GH₵1,500',top:'GH₵1,500',stars:4,min:'GH₵1',instant:true,cashout:false,stream:true,sports:150,lic:'GCA Licensed',nodep:false,badge:'',terms:'Code MBMAX. 300% match. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'SB',bg:'#E71D29',tc:'#fff',name:'Sportybet Ghana',url:'https://www.sportybet.com/gh/',tag:"Ghana's #1 Sports Betting App",off:'150% Welcome Bonus – Up to GH₵500 Free Bet',top:'GH₵500',stars:5,min:'GH₵1',instant:true,cashout:true,stream:false,sports:30,lic:'GCA Licensed',nodep:false,badge:'hot',terms:'Min deposit GH₵1. 150% as Free Bet Gifts. Min odds 3.15. 7-day expiry. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Ghana',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'GH₵5',instant:true,cashout:true,stream:false,sports:57,lic:'GCA Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Ghana',url:'https://www.betway.com/en-gh/',tag:'Super Group – Top 3 in West Africa',off:'50% Welcome Bonus – Up to GH₵200',top:'GH₵200',stars:5,min:'GH₵2',instant:true,cashout:true,stream:true,sports:28,lic:'GCA Licensed',nodep:false,badge:'',terms:'50% match up to GH₵200. MTN MoMo accepted. Wagering requirements apply. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Ghana',url:'https://22bet.com',tag:'100% Bonus – GPL & International',off:'100% First Deposit Bonus – Up to GH₵1,491',top:'GH₵1,491',stars:4,min:'GH₵5',instant:true,cashout:true,stream:false,sports:35,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match up to GH₵1,491. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'BT',bg:'#FCED0E',tc:'#1B3A7A',name:'Betika Ghana',url:'https://www.betika.com/en-gh/',tag:"Kenya's #1 Brand – Expanded to Ghana",off:'Free Bet Gifts + GPL Markets',top:'Free Bets',stars:4,min:'GH₵2',instant:true,cashout:true,stream:false,sports:20,lic:'GCA Licensed',nodep:true,badge:'new',terms:'Register and verify. Free bet on signup. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money','Visa']},
{abbr:'SP+',bg:'#63FD8C',tc:'#111',name:'Supabets Ghana',url:'https://www.supabets.com/',tag:'South African Brand – Expanded to Ghana',off:'Free Bet + Deposit Match Bonus',top:'Free Bet + Match',stars:4,min:'GH₵5',instant:true,cashout:true,stream:false,sports:25,lic:'GCA Licensed',nodep:true,badge:'new',terms:'Free bet on registration. Deposit match on first deposit. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'PB',bg:'#FF4500',tc:'#fff',name:'Premier Bet Ghana',url:'https://www.premierbet.com',tag:'20+ African Markets – Retail & Online',off:'100% Welcome Bonus on First Deposit',top:'100% Match',stars:3,min:'GH₵5',instant:true,cashout:false,stream:false,sports:20,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo accepted. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Bank Transfer','Visa']},
{abbr:'BTA',bg:'#FF3C01',tc:'#fff',name:'Betano Ghana',url:'https://betano.com',tag:'Kaizen Gaming – Committed to Ghana Market',off:'100% First Deposit Bonus – Up to GH₵500',top:'GH₵500',stars:4,min:'GH₵5',instant:true,cashout:true,stream:true,sports:30,lic:'GCA Licensed',nodep:false,badge:'new',terms:'100% match up to GH₵500. Wager x5. Min odds 1.50. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'BK',bg:'#001041',tc:'#fff',name:'BetKing Ghana',url:'https://www.betking.com',tag:'Nigerian Brand – Fast Growing in Ghana',off:'200% Welcome Bonus on First Deposit',top:'200% Match',stars:3,min:'GH₵5',instant:true,cashout:true,stream:false,sports:25,lic:'GCA Licensed',nodep:false,badge:'',terms:'200% match on first deposit. Wagering requirements apply. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'Betpawa Ghana',url:'https://www.betpawa.com.gh',tag:'Low Stakes Jackpot – Win Big from GH₵1',off:'Weekly Jackpot – Win Up to GH₵100,000 from GH₵1',top:'GH₵100k Jackpot',stars:4,min:'GH₵1',instant:true,cashout:false,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'Bet from GH₵1 on jackpot products. MTN MoMo and Vodafone Cash. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo']},
{abbr:'SCB',bg:'#006400',tc:'#fff',name:'Soccabet',url:'https://www.soccabet.com.gh',tag:"Ghana's Football Specialist",off:'100% Welcome Bonus – Up to GH₵200',top:'GH₵200',stars:4,min:'GH₵1',instant:true,cashout:true,stream:false,sports:20,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match up to GH₵200. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'MS',bg:'#FFCA27',tc:'#111',name:'MSport Ghana',url:'https://www.msport.com',tag:'200% Bonus – Fast Growing in West Africa',off:'200% Welcome Bonus – Up to GH₵500',top:'GH₵500',stars:3,min:'GH₵5',instant:true,cashout:true,stream:false,sports:20,lic:'GCA Licensed',nodep:false,badge:'',terms:'200% on first deposit up to GH₵500. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']},
{abbr:'BBR',bg:'#D32F2F',tc:'#fff',name:'BetBoro',url:'https://www.betboro.com',tag:'Boros – GPL & International Markets',off:'100% Welcome Bonus – Up to GH₵300',top:'GH₵300',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:18,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match up to GH₵300. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'BFX',bg:'#FF8F00',tc:'#fff',name:'BetFox',url:'https://www.betfox.com.gh',tag:'Fox Sharp Odds – GPL Specialist',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:18,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'KDB',bg:'#1565C0',tc:'#fff',name:'Keedbet',url:'https://www.keedbet.com',tag:'Keed – Speed & Odds in Ghana',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash']},
{abbr:'LCW',bg:'#F9A825',tc:'#111',name:'Luckywin',url:'https://www.luckywin.com.gh',tag:'Lucky Win – GPL & AFCON Markets',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'PRD',bg:'#7B1FA2',tc:'#fff',name:'Pridebet Ghana',url:'https://www.pridebet.com',tag:'Pride of Ghana Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:18,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'BNG',bg:'#E91E63',tc:'#fff',name:'BingoBets',url:'https://www.bingobets.com.gh',tag:'Bingo & Sports – Win Every Day',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash']},
{abbr:'WSL',bg:'#00BCD4',tc:'#fff',name:'WinSlots',url:'https://www.winslots.com.gh',tag:'Slots & Sports – All-in-One',off:'100% First Deposit Bonus + Spins',top:'100% + Spins',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match + free spins. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash']},
{abbr:'WWG',bg:'#43A047',tc:'#fff',name:'WinWinGame',url:'https://www.winwingame.com',tag:'Win Win – Both Teams Score in Ghana',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash']},
{abbr:'CHP',bg:'#FFC107',tc:'#111',name:'Championbet Ghana',url:'https://www.championbet.com',tag:'Champions Play Here – GPL Markets',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:18,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'MBA',bg:'#1B5E20',tc:'#fff',name:'MyBetAfrica',url:'https://www.mybetafrica.com',tag:'Africa-First Betting Platform',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:18,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'PRS',bg:'#6A1B9A',tc:'#fff',name:'Pridespins',url:'https://www.pridespins.com',tag:'Pride Spins – Casino & Sports',off:'100% Bonus + Free Spins',top:'100% + Spins',stars:3,min:'GH₵2',instant:true,cashout:true,stream:false,sports:15,lic:'GCA Licensed',nodep:false,badge:'',terms:'100% match + free spins on casino. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash']},
{abbr:'ODG',bg:'#3CC71B',tc:'#111',name:'Odibets Ghana',url:'https://www.odibets.com',tag:'Odi – Win & Keep Winning in Ghana',off:'Free Bet on Registration',top:'Free Bet',stars:4,min:'GH₵1',instant:true,cashout:true,stream:false,sports:20,lic:'GCA Licensed',nodep:true,badge:'',terms:'Free bet on registration. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','AirtelTigo Money']},
{abbr:'BB',bg:'#FFE60F',tc:'#1C1E24',name:'Bangbet Ghana',url:'https://www.bangbet.com',tag:'Low Minimum – GPL & International',off:'Deposit GH₵5, Get GH₵20 Free Bet',top:'GH₵20 Free',stars:3,min:'GH₵5',instant:true,cashout:false,stream:false,sports:20,lic:'GCA Licensed',nodep:false,badge:'',terms:'Deposit GH₵5 min and get GH₵20 free bet. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Vodafone Cash','Visa','Mastercard']}
],
ZA:[
{abbr:'BTB',bg:'#1B5E20',tc:'#fff',name:'Bettabets',url:'https://track.bettapartners.co.za/o/zNV2Pk?lpage=AjB-aC&site_id=777',tag:'SA Local Brand – PSL & Cricket',off:'R200 Free Bet on First Deposit',top:'R200 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'hot',terms:'R200 free bet on first deposit. FICA required. Min odds 1.50. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'BX',bg:'#0D47A1',tc:'#fff',name:'BetXchange',url:'https://track.trkbxa.click/o/yDSAGh?lpage=m0gk2w&site_id=1226',tag:'SA Betting Exchange – Competitive Odds',off:'R200 Free Bet on First Deposit',top:'R200 Free',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:22,lic:'WCGRB Licensed',nodep:false,badge:'hot',terms:'R200 free bet on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard','Instant EFT']},
{abbr:'TTC',bg:'#CC0000',tc:'#fff',name:'TicTacBets',url:'https://trackrt.tictacbets.co.za/o/zdY0CA?site_id=1023',tag:'SA-Owned Since 2015 – 25 Free Spins No Deposit',off:'25 Free Spins + 100% Match Up to R5,000 + 50 Spins',top:'R5,000 + 75 Spins',stars:4,min:'R5',instant:true,cashout:true,stream:false,sports:30,lic:'NCGLB Licensed',nodep:true,badge:'hot',terms:'25 free spins on registration. 100% match up to R5,000 + 50 spins on first deposit. FICA required. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT','1Voucher','Ozow','Zapper','Apple Pay']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari South Africa',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:57,lic:'NGB Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner South Africa',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to R2,340',top:'R2,340',stars:4,min:'R20',instant:true,cashout:true,stream:true,sports:40,lic:'International',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to R2,340. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet South Africa',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to R4,500',top:'R4,500',stars:4,min:'R20',instant:true,cashout:false,stream:true,sports:150,lic:'International',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to R4,500. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa South Africa',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to R3,600',top:'R3,600',stars:4,min:'R20',instant:true,cashout:true,stream:true,sports:50,lic:'International',nodep:false,badge:'new',terms:'200% match on first deposit up to R3,600. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets',url:'https://www.hollywoodbets.net/',tag:"South Africa's Largest – 80+ Physical Outlets",off:'R25 Free Bet + 50 Free Spins – No Deposit Required!',top:'R25 No Deposit',stars:5,min:'R0',instant:true,cashout:true,stream:true,sports:28,lic:'WCGRB Licensed',nodep:true,badge:'hot',terms:'No deposit required. R25 free bet + 50 free spins after registration + FICA. Must use within 24 hours. Min odds 0.5. Wager once. Spin winnings wager 5x. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard','Instant EFT']},
{abbr:'SUP',bg:'#63FD8C',tc:'#111',name:'Supabets',url:'https://www.supabets.com/',tag:'R50 Free Bet + R5,000 Match + 100 Spins',off:'R50 Free Bet + 100% Match Up to R5,000 + 100 Spins',top:'R5,000',stars:5,min:'R10',instant:true,cashout:true,stream:true,sports:25,lic:'NGB Licensed',nodep:true,badge:'hot',terms:'R50 free bet on registration + FICA. 100% match on first deposit up to R5,000. Rollover 3x at min odds 2.0. 15 days. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT','Blue Voucher']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway South Africa',url:'https://www.betway.com/en-za/',tag:'Super Group – R1 Million Prize Drop',off:'R10 Extra Bet + 10 Spins + 10 Flights + R1M Drop',top:'R1M Prize',stars:4,min:'R5',instant:true,cashout:true,stream:true,sports:28,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'Code SPMAX. R10 extra bet + 10 spins + 10 free flights after R50 deposit. Random R1M MEGA prize. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard','Instant EFT']},
{abbr:'10B',bg:'#1A1A1A',tc:'#FFD700',name:'10bet South Africa',url:'https://www.10bet.co.za',tag:'WCGRB Licensed – Premium Sports & Casino',off:'100% First Deposit Bonus – Up to R2,000',top:'R2,000',stars:4,min:'R20',instant:true,cashout:true,stream:false,sports:30,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'100% match up to R2,000 on first deposit. Wagering requirements apply. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'EB',bg:'#0D47A1',tc:'#fff',name:'Easybet',url:'https://www.easybet.co.za',tag:'Top 5 in SA – Data-Free App Available',off:'150% Welcome Bonus – Up to R4,000',top:'R4,000',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:25,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'150% match up to R4,000. Data-free app available. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT','Blue Voucher']},
{abbr:'WS',bg:'#002D72',tc:'#fff',name:'World Sports Betting',url:'https://www.wsb.co.za',tag:'SA Pioneer – Est. 2000 – PSL & More',off:'Up to R2,000 Free Bet on First Deposit',top:'R2,000',stars:4,min:'R20',instant:true,cashout:true,stream:false,sports:25,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'Register and deposit to claim free bet up to R2,000. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard']},
{abbr:'SPB',bg:'#076da7',tc:'#fff',name:'Sportingbet SA',url:'https://www.sportingbet.co.za',tag:'International Brand – PSL & Cricket',off:'100% Welcome Bonus Up to R1,000',top:'R1,000',stars:3,min:'R20',instant:true,cashout:true,stream:false,sports:22,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'100% match up to R1,000. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Visa','Mastercard','Instant EFT']},
{abbr:'SUN',bg:'#001435',tc:'#FFAB09',name:'Sunbet',url:'https://www.sunbet.co.za',tag:'Sun International Casino Backed',off:'R300 Free Bet on Signup',top:'R300 Free',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'WCGRB Licensed',nodep:true,badge:'new',terms:'R300 free bet on registration + FICA. 7-day expiry. Min odds 1.50. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa','Mastercard']},
{abbr:'BF',bg:'#E20000',tc:'#fff',name:'Betfred SA',url:'https://www.betfred.co.za',tag:'UK Brand – PSL & Rugby Coverage',off:'100% Welcome Bonus – Up to R1,500',top:'R1,500',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:25,lic:'WCGRB Licensed',nodep:false,badge:'new',terms:'100% match up to R1,500 on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'JSB',bg:'#1a237e',tc:'#fff',name:'JSB Sport',url:'https://www.jsbsport.co.za',tag:'Local SA Bookmaker – Wide Sports Coverage',off:'100% Deposit Match – Up to R1,000',top:'R1,000',stars:3,min:'R10',instant:true,cashout:false,stream:false,sports:20,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'100% match up to R1,000 on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'PAB',bg:'#FF6B00',tc:'#fff',name:'Playabet',url:'https://www.playabet.co.za',tag:'SA Online Bookmaker – PSL & Cricket',off:'R500 Welcome Bonus on First Deposit',top:'R500',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:22,lic:'NGB Licensed',nodep:false,badge:'',terms:'R500 bonus on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'PLB',bg:'#6A1B9A',tc:'#fff',name:'Playbet',url:'https://www.playbet.co.za',tag:'SA Bookmaker – Sports & Casino',off:'100% Deposit Bonus – Up to R2,000',top:'R2,000',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:22,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'100% match up to R2,000 on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'SCH',bg:'#2E7D32',tc:'#fff',name:'Soccershop',url:'https://www.soccershop.co.za',tag:'SA Soccer Specialist – PSL & More',off:'R250 Free Bet on Registration',top:'R250 Free',stars:3,min:'R10',instant:true,cashout:false,stream:false,sports:15,lic:'NGB Licensed',nodep:true,badge:'',terms:'R250 free bet on registration + FICA. Min odds 1.50. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'1BT',bg:'#B71C1C',tc:'#fff',name:'FirstBet',url:'https://www.firstbet.co.za',tag:'SA Bookmaker – Fast Payouts',off:'100% First Deposit Bonus – Up to R1,500',top:'R1,500',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'100% match up to R1,500 on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'TBB',bg:'#004D40',tc:'#fff',name:'Thababet',url:'https://www.thababet.co.za',tag:'SA Local Brand – PSL Specialists',off:'R300 Welcome Bonus on Signup',top:'R300',stars:3,min:'R10',instant:true,cashout:false,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'new',terms:'R300 bonus on first deposit. FICA required. Wagering requirements apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'YPL',bg:'#FF6F00',tc:'#fff',name:'YesPlay',url:'https://www.yesplay.bet',tag:'Yes to Big Wins – SA Sports & Casino',off:'100% Welcome Bonus – Up to R1,000',top:'R1,000',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:25,lic:'NGB Licensed',nodep:false,badge:'',terms:'100% match up to R1,000. FICA required. Wagering apply. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT','Visa']},
{abbr:'SSB',bg:'#0D47A1',tc:'#fff',name:'SuperSportBet',url:'https://www.supersportbet.com',tag:'SuperSport Powered – SA Sport Leader',off:'R200 Free Bet on First Deposit',top:'R200 Free',stars:4,min:'R10',instant:true,cashout:true,stream:true,sports:30,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R200 free bet on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'VGB',bg:'#C62828',tc:'#fff',name:'VegasBets',url:'https://www.vegasbets.co.za',tag:'Vegas-Style Betting in SA',off:'R200 Welcome Bonus on First Deposit',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:22,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT','Visa','Mastercard']},
{abbr:'GBT',bg:'#2E7D32',tc:'#fff',name:'Gbets',url:'https://www.gbets.co.za',tag:'SA & Lesotho Brand – PSL Coverage',off:'R200 Free Bet on Registration',top:'R200 Free',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:25,lic:'NGB Licensed',nodep:true,badge:'',terms:'R200 free bet on registration + FICA. PSL and rugby covered. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'GOR',bg:'#FF6F00',tc:'#fff',name:'Goldrush',url:'https://www.goldrushgaming.co.za',tag:"SA's Slots & Sports Leader",off:'R100 Free Bet on Registration',top:'R100 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:true,badge:'',terms:'R100 free bet on registration. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Visa']},
{abbr:'JPC',bg:'#FFD700',tc:'#111',name:'JackpotCity',url:'https://www.jackpotcitycasino.com',tag:'International Casino Brand in SA',off:'Up to R10,000 Welcome Package',top:'R10,000',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:0,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'Welcome package up to R10,000 across first deposits. FICA required. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT','Neteller']},
{abbr:'L247',bg:'#1A237E',tc:'#fff',name:'Lotto247',url:'https://www.lotto247.com',tag:'Lotto & Sports – SA Online Betting',off:'R100 Free Bet on Registration',top:'R100 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:15,lic:'NGB Licensed',nodep:true,badge:'',terms:'R100 free bet on registration. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Visa','Mastercard','Instant EFT']},
{abbr:'LTL',bg:'#E53935',tc:'#fff',name:'Lottoland',url:'https://www.lottoland.co.za',tag:'World Lotteries + SA Sports Betting',off:'R50 Free Bet on Registration',top:'R50 Free',stars:3,min:'R5',instant:true,cashout:false,stream:false,sports:15,lic:'NGB Licensed',nodep:true,badge:'',terms:'R50 free bet on registration. FICA required. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT']},
{abbr:'LTS',bg:'#F57F17',tc:'#fff',name:'Lottostar',url:'https://www.lottostar.co.za',tag:'Biggest Jackpots in SA',off:'R50 Welcome Bonus',top:'R50',stars:3,min:'R5',instant:true,cashout:false,stream:false,sports:10,lic:'NGB Licensed',nodep:false,badge:'',terms:'R50 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['Visa','Mastercard','Instant EFT']},
{abbr:'PTB',bg:'#1565C0',tc:'#fff',name:'Pantherbet',url:'https://www.pantherbet.co.za',tag:'Panther Speed – Instant Payouts',off:'R200 Welcome Bonus on First Deposit',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT','Visa']},
{abbr:'NEB',bg:'#00838F',tc:'#fff',name:'Neobet',url:'https://www.neobet.co.za',tag:'New Era Betting in South Africa',off:'R300 Welcome Bonus',top:'R300',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:22,lic:'NGB Licensed',nodep:false,badge:'new',terms:'R300 welcome bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT','Visa']},
{abbr:'PTS',bg:'#4CAF50',tc:'#fff',name:'PlayTsogo',url:'https://www.tsogosun.com',tag:'Tsogo Sun Gaming – Premium SA Brand',off:'R100 Free Bet on Registration',top:'R100 Free',stars:4,min:'R10',instant:true,cashout:true,stream:true,sports:25,lic:'WCGRB Licensed',nodep:true,badge:'',terms:'R100 free bet on registration. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'TAB',bg:'#1A237E',tc:'#fff',name:'TAB',url:'https://www.tab.co.za',tag:'The Australian Brand – SA Racing & Sport',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:true,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 welcome bonus. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'LUL',bg:'#7B1FA2',tc:'#fff',name:'Lulabet',url:'https://www.lulabet.co.za',tag:'Lula – Local SA Brand',off:'R150 Free Bet on Registration',top:'R150 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:true,badge:'',terms:'R150 free bet on registration. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']},
{abbr:'KGB',bg:'#B71C1C',tc:'#fff',name:'Kingbets',url:'https://www.kingbets.co.za',tag:'King of SA Sports Betting',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 welcome bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT','Visa']},
{abbr:'ITB',bg:'#1B5E20',tc:'#fff',name:'Interbet',url:'https://www.interbet.co.za',tag:'SA Veteran – Est. 2000',off:'R200 Free Bet on First Deposit',top:'R200 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R200 free bet on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'JAB',bg:'#E65100',tc:'#fff',name:'Jabulabets',url:'https://www.jabulabets.co.za',tag:'Jabula – Joy of Winning in SA',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'INK',bg:'#4527A0',tc:'#fff',name:'InkwenkweziBets',url:'https://www.inkwenkwezibets.co.za',tag:'Star Bets – Eastern Cape Local Brand',off:'R200 Free Bet on Registration',top:'R200 Free',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'ECGBB Licensed',nodep:true,badge:'',terms:'R200 free bet on registration. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'MZB',bg:'#006064',tc:'#fff',name:'Mzansibet',url:'https://www.mzansibet.co.za',tag:'Mzansi Pride – Local SA Bookmaker',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']},
{abbr:'FTB',bg:'#F57F17',tc:'#fff',name:'FatBet',url:'https://www.fatbet.co.za',tag:'Fat Odds – SA Sports Specialist',off:'R200 Welcome Bonus on First Deposit',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT','Visa']},
{abbr:'BCZ',bg:'#263238',tc:'#fff',name:'Betcoza',url:'https://www.betcoza.co.za',tag:'Bet Co ZA – SA Local Platform',off:'R150 Welcome Bonus',top:'R150',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R150 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']},
{abbr:'EBT',bg:'#0D47A1',tc:'#fff',name:'eBet',url:'https://www.ebet.co.za',tag:'SA & Angola – Multi-Market Brand',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'PLB',bg:'#00897B',tc:'#fff',name:'Playabets',url:'https://www.playabets.co.za',tag:'Play & Win – SA Betting Platform',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'PCZ',bg:'#1565C0',tc:'#fff',name:'Playcoza',url:'https://www.playcoza.co.za',tag:'Play Co ZA – SA Sports',off:'R200 First Deposit Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT','Visa']},
{abbr:'SCR',bg:'#2E7D32',tc:'#fff',name:'Scorebet',url:'https://www.scorebet.co.za',tag:'Score Big – SA Sportsbook',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'PKB',bg:'#1A237E',tc:'#fff',name:'Pokerbet',url:'https://www.pokerbet.co.za',tag:'Poker & Sports – SA Licensed',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:15,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT','Visa']},
{abbr:'VRB',bg:'#C62828',tc:'#fff',name:'VirginBet',url:'https://www.virginbet.co.za',tag:'Virgin Brand – SA Sports & Casino',off:'R200 Welcome Bonus on First Deposit',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'SWF',bg:'#006064',tc:'#fff',name:'SwiftySports',url:'https://www.swiftysports.co.za',tag:'Swift Payouts – SA Specialist',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']},
{abbr:'TPB',bg:'#4E342E',tc:'#fff',name:'Topbet',url:'https://www.topbet.co.za',tag:'SA Veteran Bookmaker – Est. 2000s',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'BJT',bg:'#0288D1',tc:'#fff',name:'BetJets',url:'https://www.betjets.co.za',tag:'Fly High – SA Sports Betting',off:'R200 First Deposit Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'BOP',bg:'#303F9F',tc:'#fff',name:'BetOlimp',url:'https://www.betolimp.co.za',tag:'Olympic Odds – SA Sportsbook',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:20,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT','Visa']},
{abbr:'BSH',bg:'#4A148C',tc:'#fff',name:'BetShezi',url:'https://www.betshezi.co.za',tag:'Shezi Style – KwaZulu-Natal Specialist',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'KZNGLB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'LFH',bg:'#FF6F00',tc:'#fff',name:'Luckyfish',url:'https://www.luckyfish.co.za',tag:'Lucky Fish – Bite Into Big Winnings',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']},
{abbr:'MBT',bg:'#00695C',tc:'#fff',name:'Mbet South Africa',url:'https://www.mbet.co.za',tag:'M Bet – Mobile-First SA Betting',off:'R200 First Deposit Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Instant EFT']},
{abbr:'WSB',bg:'#1B5E20',tc:'#fff',name:'WSB',url:'https://www.wsb.co.za',tag:'World Sports Betting – SA Pioneer',off:'R300 Welcome Bonus on First Deposit',top:'R300',stars:4,min:'R10',instant:true,cashout:true,stream:false,sports:25,lic:'WCGRB Licensed',nodep:false,badge:'',terms:'R300 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Standard Bank','Nedbank','Capitec','Instant EFT']},
{abbr:'YRB',bg:'#E65100',tc:'#fff',name:'YourBet',url:'https://www.yourbet.co.za',tag:'Your Bet – Personalised SA Betting',off:'R200 Welcome Bonus',top:'R200',stars:3,min:'R10',instant:true,cashout:true,stream:false,sports:18,lic:'NGB Licensed',nodep:false,badge:'',terms:'R200 bonus on first deposit. FICA required. T&Cs. 18+.',pms:['FNB','Nedbank','Capitec','Instant EFT']}
],
TZ:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Tanzania',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Highest in Tanzania',off:'200% First Deposit Bonus – Up to TSh 500,000',top:'TSh 500,000',stars:4,min:'TSh 500',instant:true,cashout:true,stream:true,sports:50,lic:'GBT Licensed',nodep:false,badge:'',terms:'200% match up to TSh 500,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Halotel Pesa','Visa']},
{abbr:'BT',bg:'#FCED0E',tc:'#1B3A7A',name:'Betika Tanzania',url:'https://www.betika.com',tag:'East Africa\'s Leading Brand – Now in TZ',off:'Free Bet on Signup + TSh 5,000 Welcome Bonus',top:'TSh 5,000',stars:5,min:'TSh 200',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:true,badge:'hot',terms:'Register and verify. Free bet + TSh 5,000 welcome bonus on first deposit. M-Pesa (Vodacom). T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Bank Transfer']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Tanzania',url:'https://www.sportpesa.co.tz',tag:'#1 Jackpot Brand in East Africa',off:'250% Karibu Gift on First Deposit',top:'250% Match',stars:5,min:'TSh 200',instant:true,cashout:true,stream:true,sports:30,lic:'GBT Licensed',nodep:false,badge:'hot',terms:'250% Karibu Gift on first deposit. M-Pesa and Airtel Money. Mega Jackpot weekly. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Tanzania',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'TSh 500',instant:true,cashout:true,stream:false,sports:57,lic:'GBT Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Halotel Pesa','Visa']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Tanzania',url:'https://www.betway.co.tz',tag:'International Brand – Fast Payouts',off:'50% Welcome Bonus – Up to TSh 120,000',top:'TSh 120,000',stars:4,min:'TSh 500',instant:true,cashout:true,stream:true,sports:28,lic:'GBT Licensed',nodep:false,badge:'',terms:'50% match up to TSh 120,000. M-Pesa and Airtel Money. Wagering requirements apply. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Visa','Mastercard']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Tanzania',url:'https://22bet.com',tag:'100% Bonus – TPL & International',off:'100% First Deposit Bonus – Up to TSh 460,000',top:'TSh 460,000',stars:4,min:'TSh 500',instant:true,cashout:true,stream:false,sports:35,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match up to TSh 460,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Visa','Mastercard']},
{abbr:'PB',bg:'#FF4500',tc:'#fff',name:'Premierbet Tanzania',url:'https://www.premierbet.com',tag:'20+ African Markets – Retail Shops',off:'100% Welcome Bonus on First Deposit',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:false,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Mobile money accepted. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Bank Transfer']},
{abbr:'BGB',bg:'#E91E63',tc:'#fff',name:'BongoBongo Tanzania',url:'https://bongobongo.co.tz',tag:'East Africa Jackpot Leader',off:'100% Welcome Bonus – Up to TSh 50,000',top:'TSh 50,000',stars:4,min:'TSh 200',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match up to TSh 50,000. M-Pesa Vodacom. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'BB',bg:'#FFE60F',tc:'#1C1E24',name:'Bangbet Tanzania',url:'https://www.bangbet.com',tag:'Low Minimum – TPL Markets',off:'Deposit TSh 1,000 Get TSh 5,000 Free',top:'TSh 5,000',stars:3,min:'TSh 1,000',instant:true,cashout:false,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'Low stakes offer on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'WSF',bg:'#00695C',tc:'#fff',name:'WasafiBet',url:'https://www.wasafibet.co.tz',tag:'Wasafi – Tanzania Media Brand',off:'100% Welcome Bonus – Up to TSh 50,000',top:'TSh 50,000',stars:4,min:'TSh 500',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'hot',terms:'100% match up to TSh 50,000. M-Pesa Vodacom. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Bank Transfer']},
{abbr:'SLP',bg:'#1565C0',tc:'#fff',name:'SlotPesa',url:'https://www.slotpesa.com',tag:'Tanzania Slots & Sports Leader',off:'100% Bonus on First Deposit',top:'100% Match',stars:4,min:'TSh 200',instant:true,cashout:true,stream:false,sports:15,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'MBT',bg:'#00695C',tc:'#fff',name:'Mbet Tanzania',url:'https://www.mbet.co.tz',tag:'Mobile Betting – TPL Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:18,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'PMB',bg:'#37474F',tc:'#fff',name:'PMBet',url:'https://www.pmbet.co.tz',tag:'PM Bet – Tanzania Sports Coverage',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:18,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'PGB',bg:'#1B5E20',tc:'#fff',name:'Pigabet',url:'https://www.pigabet.co.tz',tag:'Piga – Hit the Jackpot Daily',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'TSh 200',instant:true,cashout:true,stream:false,sports:15,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'KGB',bg:'#B71C1C',tc:'#fff',name:'KingBet Tanzania',url:'https://www.kingbet.co.tz',tag:'King of Tanzanian Betting',off:'100% Bonus on First Deposit',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:18,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'PAM',bg:'#880E4F',tc:'#fff',name:'PariMatch Tanzania',url:'https://www.parimatch.com',tag:'International – 200+ Live Events',off:'100% Welcome Bonus – Up to TSh 230,000',top:'TSh 230,000',stars:4,min:'TSh 500',instant:true,cashout:true,stream:true,sports:40,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match up to TSh 230,000. Wagering apply. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Visa','Mastercard']},
{abbr:'MRD',bg:'#4527A0',tc:'#fff',name:'MeridianBet Tanzania',url:'https://www.meridianbet.co.tz',tag:'Balkan Brand – Tanzania Football Expert',off:'100% Welcome Bonus',top:'100% Match',stars:4,min:'TSh 500',instant:true,cashout:true,stream:false,sports:25,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa','Visa']},
{abbr:'BKS',bg:'#0288D1',tc:'#fff',name:'Bikosport',url:'https://www.bikosport.co.tz',tag:'Biko – Tanzania Local Sports Brand',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:15,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'THR',bg:'#311B92',tc:'#fff',name:'ThroneBet Tanzania',url:'https://www.thronebet.co.tz',tag:'Sit on the Throne – Big Odds',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:18,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'GSB',bg:'#2E7D32',tc:'#fff',name:'GSB Tanzania',url:'https://www.gsbet.co.tz',tag:'Great Sports Betting – East Africa',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'HLT',bg:'#430084',tc:'#fff',name:'Helabet Tanzania',url:'https://www.helabet.com',tag:'100+ Live Markets – Tanzania',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:25,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Visa']},
{abbr:'SKT',bg:'#00838F',tc:'#fff',name:'Sokabet Tanzania',url:'https://www.sokabet.co.tz',tag:'Soka – Football Specialist TZ',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Tigo Pesa']},
{abbr:'888T',bg:'#1A237E',tc:'#fff',name:'888Bet Tanzania',url:'https://www.888bet.co.tz',tag:'888 – Premium Odds for Tanzania',off:'100% Welcome Bonus – Up to TSh 100,000',top:'TSh 100,000',stars:3,min:'TSh 500',instant:true,cashout:true,stream:false,sports:20,lic:'GBT Licensed',nodep:false,badge:'',terms:'100% match up to TSh 100,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa (Vodacom)','Airtel Money','Visa','Mastercard']}
],
UG:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Uganda',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Uganda\'s Highest Offer',off:'200% First Deposit Bonus – Up to USh 3,600,000',top:'USh 3.6M',stars:4,min:'USh 1,000',instant:true,cashout:true,stream:true,sports:50,lic:'UNCS Licensed',nodep:false,badge:'',terms:'200% match up to USh 3,600,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Visa','Mastercard']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Uganda',url:'https://www.betway.co.ug',tag:'Uganda\'s Most Trusted International Brand',off:'50% Welcome Bonus – Up to USh 180,000',top:'USh 180,000',stars:5,min:'USh 1,000',instant:true,cashout:true,stream:true,sports:28,lic:'UNCS Licensed',nodep:false,badge:'hot',terms:'50% match up to USh 180,000. MTN MoMo and Airtel Money. Wager 3x. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer','Visa','Mastercard']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Uganda',url:'https://www.sportpesa.co.ug',tag:'Mega Jackpot Weekly',off:'200% Karibu Gift on First Deposit',top:'200% Match',stars:4,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:25,lic:'UNCS Licensed',nodep:false,badge:'',terms:'200% Karibu Gift on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Uganda',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:57,lic:'UNCS Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Visa','Mastercard']},
{abbr:'BT',bg:'#FCED0E',tc:'#1B3A7A',name:'Betika Uganda',url:'https://www.betika.com/en-ug/',tag:'Expanded from Kenya – Free Bet Welcome',off:'Free Bet on Signup + Uganda Leagues',top:'Free Bets',stars:4,min:'USh 500',instant:true,cashout:true,stream:false,sports:20,lic:'UNCS Licensed',nodep:true,badge:'new',terms:'Register and verify. Free bet on signup. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'Betpawa Uganda',url:'https://www.betpawa.ug',tag:'Jackpot from USh 500 – Big Weekly Prizes',off:'Weekly Jackpot – Bet from USh 500',top:'Jackpot USh 500',stars:4,min:'USh 500',instant:true,cashout:false,stream:false,sports:15,lic:'UNCS Licensed',nodep:false,badge:'',terms:'Bet from USh 500 on jackpot products. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Uganda',url:'https://22bet.com',tag:'100% Bonus – EPL & UPL Markets',off:'100% First Deposit Bonus – Up to USh 3,200,000',top:'USh 3.2M',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:35,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match up to USh 3,200,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Visa','Mastercard']},
{abbr:'KGW',bg:'#1B5E20',tc:'#fff',name:'Kagwirawo',url:'https://www.kagwirawo.com',tag:"Uganda's Jackpot Pioneer",off:'Weekly Jackpot from USh 500',top:'Jackpot',stars:4,min:'USh 500',instant:true,cashout:true,stream:false,sports:15,lic:'UNCS Licensed',nodep:false,badge:'hot',terms:'Bet from USh 500 on jackpots. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'FTB',bg:'#E65100',tc:'#fff',name:'Fortebet Uganda',url:'https://www.fortebet.ug',tag:"Uganda's #1 Retail & Online Brand",off:'100% Welcome Bonus – Up to USh 150,000',top:'USh 150,000',stars:4,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:25,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match up to USh 150,000. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer','Visa']},
{abbr:'ABA',bg:'#4527A0',tc:'#fff',name:'Ababet Uganda',url:'https://www.ababet.com',tag:'Aba – Bet Boldly in Uganda',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'SEM',bg:'#006064',tc:'#fff',name:'Semabet Uganda',url:'https://www.semabet.com',tag:'Sema – Uganda Sports Specialist',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'KWB',bg:'#1565C0',tc:'#fff',name:'Kiwibet Uganda',url:'https://www.kiwibet.com',tag:'Kiwi – Fresh Odds Every Day',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'GKU',bg:'#FF8F00',tc:'#fff',name:'GameKaya Uganda',url:'https://www.gamekaya.com',tag:'Game Kaya – Win Big in Uganda',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'CHU',bg:'#FFC107',tc:'#111',name:'Championbet Uganda',url:'https://www.championbet.com',tag:'Champions Play Here – UPL Markets',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'SHG',bg:'#6D4C41',tc:'#fff',name:'SaharaGames',url:'https://www.saharagames.net',tag:'Sahara – Vast Odds Landscape',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'KSB',bg:'#B71C1C',tc:'#fff',name:'KingssportsBetting',url:'https://www.kingssportsbetting.com',tag:'Kings of Uganda Sports Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:15,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'ADM',bg:'#1A237E',tc:'#fff',name:'Admiralbet Uganda',url:'https://www.admiralbet.ug',tag:'Admiral – European Quality in Uganda',off:'100% Welcome Bonus – Up to USh 200,000',top:'USh 200,000',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:25,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match up to USh 200,000. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Visa','Mastercard']},
{abbr:'BSU',bg:'#4CAF50',tc:'#fff',name:'Betsports Uganda',url:'https://www.betsports.ug',tag:'Uganda Sports Betting Expert',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:15,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'GSU',bg:'#2E7D32',tc:'#fff',name:'GSB Uganda',url:'https://www.gsbet.co.tz',tag:'Great Sports Betting – East Africa',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:20,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'BGU',bg:'#E91E63',tc:'#fff',name:'BongoBongo Uganda',url:'https://bongobongo.co.tz',tag:'East Africa Jackpot Network',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:18,lic:'UNCS Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money']},
{abbr:'BBU',bg:'#FFE60F',tc:'#1C1E24',name:'Bangbet Uganda',url:'https://www.bangbet.com',tag:'Low Minimum – UPL Coverage',off:'Deposit USh 1,000 Get Free Bet',top:'Free Bet',stars:3,min:'USh 1,000',instant:true,cashout:false,stream:false,sports:20,lic:'UNCS Licensed',nodep:false,badge:'',terms:'Low stakes deposit offer. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Bank Transfer']},
{abbr:'MSU',bg:'#FFCA27',tc:'#111',name:'MSport Uganda',url:'https://www.msport.com',tag:'200% Bonus – Growing in East Africa',off:'200% Welcome Bonus',top:'200% Match',stars:3,min:'USh 1,000',instant:true,cashout:true,stream:false,sports:20,lic:'UNCS Licensed',nodep:false,badge:'',terms:'200% on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Airtel Money','Visa','Mastercard']}
],
ZM:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Zambia',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – 50+ Sports',off:'200% First Deposit Bonus – Up to ZK 1,800',top:'ZK 1,800',stars:4,min:'ZK 5',instant:true,cashout:true,stream:true,sports:50,lic:'GLB Licensed',nodep:false,badge:'',terms:'200% match up to ZK 1,800. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Visa','Mastercard']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Zambia',url:'https://www.betway.co.zm',tag:'Zambia\'s #1 International Bookmaker',off:'50% Welcome Bonus – Up to ZK 500',top:'ZK 500',stars:5,min:'ZK 5',instant:true,cashout:true,stream:true,sports:28,lic:'GLB Licensed',nodep:false,badge:'hot',terms:'50% match up to ZK 500. MTN MoMo Zambia and Airtel Money. Wager 3x. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer','Visa']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Zambia',url:'https://www.sportpesa.co.zm',tag:'Mega Jackpot & FAZ Coverage',off:'200% Karibu Gift on First Deposit',top:'200% Match',stars:4,min:'ZK 2',instant:true,cashout:true,stream:false,sports:25,lic:'GLB Licensed',nodep:false,badge:'',terms:'200% Karibu Gift on first deposit. MTN MoMo Zambia. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Zambia',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'ZK 5',instant:true,cashout:true,stream:false,sports:57,lic:'GLB Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Visa','Mastercard']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'Betpawa Zambia',url:'https://www.betpawa.co.zm',tag:'Bet from ZK 1 – Weekly Jackpot',off:'Weekly Jackpot – Win Millions from ZK 1',top:'Jackpot ZK 1',stars:4,min:'ZK 1',instant:true,cashout:false,stream:false,sports:15,lic:'GLB Licensed',nodep:false,badge:'',terms:'Bet from ZK 1 on jackpot products. MTN MoMo Zambia. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia']},
{abbr:'BNZ',bg:'#1a6b35',tc:'#fff',name:'BonanzaBet Zambia',url:'https://www.bonanzabet.co.zm',tag:'Local Brand – Fast Zambia Payouts',off:'100% First Deposit Bonus – Up to ZK 500',top:'ZK 500',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:20,lic:'GLB Licensed',nodep:false,badge:'new',terms:'100% match on first deposit up to ZK 500. Zamtel Mobile Money accepted. T&Cs. 18+.',pms:['MTN MoMo Zambia','Zamtel Mobile Money','Bank Transfer']},
{abbr:'BLB',bg:'#F57F17',tc:'#111',name:'Bolabet Zambia',url:'https://www.bolabet.co.zm',tag:'Local Zambia Brand – FAZ & Sports Coverage',off:'100% Welcome Bonus – Up to ZK 1,000',top:'ZK 1,000',stars:3,min:'ZK 5',instant:true,cashout:false,stream:false,sports:18,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match up to ZK 1,000 on first deposit. MTN MoMo Zambia. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']},
{abbr:'BLN',bg:'#F57F17',tc:'#fff',name:'BetLion Zambia',url:'https://www.betlion.com',tag:'Lion Odds – FAZ & CAF Coverage',off:'100% Welcome Bonus – Up to ZK 500',top:'ZK 500',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:18,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match up to ZK 500. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']},
{abbr:'22Z',bg:'#024147',tc:'#fff',name:'22Bet Zambia',url:'https://22bet.com',tag:'100% Bonus – CAF & FAZ Markets',off:'100% First Deposit Bonus – Up to ZK 2,500',top:'ZK 2,500',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:35,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match up to ZK 2,500. Wager x5. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Visa','Mastercard']},
{abbr:'BWN',bg:'#006400',tc:'#fff',name:'Bwanabet',url:'https://www.bwanabet.com',tag:'Bwana – Zambia Local Brand',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:15,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']},
{abbr:'PPZ',bg:'#172BE2',tc:'#fff',name:'Paripesa Zambia',url:'https://paripesa.com',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to ZK 5,000',top:'ZK 5,000',stars:3,min:'ZK 5',instant:true,cashout:true,stream:true,sports:50,lic:'GLB Licensed',nodep:false,badge:'',terms:'200% match up to ZK 5,000. Wager x5. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Visa','Mastercard']},
{abbr:'MJZ',bg:'#880E4F',tc:'#fff',name:'Mojabet Zambia',url:'https://www.mojabet.com',tag:'Moja – One Goal, Big Wins',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:18,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']},
{abbr:'BGB',bg:'#E91E63',tc:'#fff',name:'BongoBongo Zambia',url:'https://bongobongo.co.tz',tag:'East Africa Jackpot Network',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:18,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia']},
{abbr:'GSZ',bg:'#2E7D32',tc:'#fff',name:'GSB Zambia',url:'https://www.gsbet.co.tz',tag:'Great Sports Betting – Multi-Country',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'ZK 5',instant:true,cashout:true,stream:false,sports:18,lic:'GLB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Zambia','Airtel Money Zambia','Bank Transfer']}
],
ET:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Ethiopia',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'International Bookmaker – EPL & AFCON Markets',off:'200% First Deposit Bonus – Up to Br 10,000',top:'Br 10,000',stars:4,min:'Br 50',instant:true,cashout:true,stream:true,sports:50,lic:'International',nodep:false,badge:'',terms:'200% match up to Br 10,000. Wager x5 at min odds 1.40. 30 days. T&Cs apply. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'RB',bg:'#FFFFFF',tc:'#1B5E20',name:'Rasbet',url:'https://rasbet.goaffnk.com/t/MTRfMQ==/',tag:'Rising Sportsbook for the Ethiopian Market',off:'Welcome Bonus on First Deposit',top:'Deposit Bonus',stars:3,min:'Br 50',instant:true,cashout:true,stream:false,sports:20,lic:'Licensed',nodep:false,badge:'new',terms:'Welcome bonus on first deposit. T&Cs apply. 18+.',pms:['Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Ethiopia',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'Br 50',instant:true,cashout:true,stream:false,sports:57,lic:'International',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']}
],
CI:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Côte d\'Ivoire',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Highest in Ivory Coast',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:5,min:'CFA 200',instant:true,cashout:true,stream:true,sports:50,lic:'ARJEL Licensed',nodep:false,badge:'hot',terms:'200% match up to CFA 200,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Wave','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Côte d\'Ivoire',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:4,min:'CFA 200',instant:true,cashout:false,stream:true,sports:150,lic:'ARJEL Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Wave','Visa','Mastercard']},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Côte d\'Ivoire',url:'https://22bet.com',tag:'100% Bonus – Ligue 1 CI & International',off:'100% First Deposit Bonus',top:'100% Match',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:35,lic:'ARJEL Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Wave','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Ivory Coast',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:57,lic:'ARJEL Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Wave','Visa','Mastercard']},
{abbr:'PB',bg:'#FF4500',tc:'#fff',name:'Premier Bet CI',url:'https://www.premierbet.com/ci',tag:'Licensed in Ivory Coast – Retail & Online',off:'Welcome Bonus on First Deposit',top:'Deposit Bonus',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:20,lic:'ARJEL Licensed',nodep:false,badge:'new',terms:'Welcome bonus on first deposit. Orange Money and MTN MoMo accepted. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Bank Transfer']}
],
CM:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Cameroun',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Elite One & AFCON',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:4,min:'CFA 200',instant:true,cashout:true,stream:true,sports:50,lic:'AMJ Licensed',nodep:false,badge:'',terms:'200% match up to CFA 200,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Cameroun',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – Elite One & 150+ Sports',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:4,min:'CFA 200',instant:true,cashout:false,stream:true,sports:150,lic:'AMJ Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Visa','Mastercard']},
{abbr:'PMU',bg:'#003580',tc:'#fff',name:'PMUC Cameroun',url:'https://www.pmuc.cm',tag:'State-Backed – Retail Shops & Online',off:'100% Bonus de Bienvenue – jusqu\'à CFA 50,000',top:'CFA 50,000',stars:5,min:'CFA 200',instant:true,cashout:true,stream:false,sports:20,lic:'AMJ Licensed',nodep:false,badge:'hot',terms:'100% match up to CFA 50,000. Orange Money and MTN MoMo. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Cameroon',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:57,lic:'AMJ Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Orange Money','MTN MoMo','Visa','Mastercard']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'BetPawa Cameroon',url:'https://www.betpawa.com',tag:'Jackpot from CFA 100 – Big Weekly Prizes',off:'Weekly Jackpot from CFA 100',top:'Jackpot',stars:4,min:'CFA 100',instant:true,cashout:false,stream:false,sports:15,lic:'AMJ Licensed',nodep:false,badge:'',terms:'Bet from CFA 100 on jackpots. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Orange Money','Bank Transfer']},
{abbr:'BSN',bg:'#1565C0',tc:'#fff',name:'Betsson Cameroon',url:'https://www.betsson.com',tag:'European Brand – 200+ Live Events',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:true,sports:30,lic:'AMJ Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Orange Money. T&Cs. 18+.',pms:['MTN MoMo','Orange Money','Visa','Mastercard']},
{abbr:'BTM',bg:'#880E4F',tc:'#fff',name:'Bettomax Cameroon',url:'https://www.bettomax.com',tag:'West Africa Multi-Market Brand',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:false,sports:18,lic:'AMJ Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Orange Money','Bank Transfer']},
{abbr:'ROB',bg:'#B71C1C',tc:'#fff',name:'Roisbet',url:'https://www.roisbet.com',tag:'Cameroon Local Bookmaker',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:false,sports:15,lic:'AMJ Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Orange Money']},
{abbr:'SGO',bg:'#F57F17',tc:'#fff',name:'Supergooal',url:'https://www.supergooal.com',tag:'Super Goals – Cameroon Sports',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:false,sports:15,lic:'AMJ Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo','Orange Money','Bank Transfer']}
],
SN:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Sénégal',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Ligue 1 SN & AFCON',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:4,min:'CFA 200',instant:true,cashout:true,stream:true,sports:50,lic:'ARTP Licensed',nodep:false,badge:'',terms:'200% match up to CFA 200,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','Wave','MTN MoMo','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Sénégal',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to CFA 200,000',top:'CFA 200,000',stars:4,min:'CFA 200',instant:true,cashout:false,stream:true,sports:150,lic:'ARTP Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money','Wave','MTN MoMo','Visa','Mastercard']},
{abbr:'PMU',bg:'#003580',tc:'#fff',name:'PMU Sénégal',url:'https://www.pmu.sn',tag:'Official State Bookmaker – Retail & Online',off:'100% Bonus – jusqu\'à CFA 50,000',top:'CFA 50,000',stars:5,min:'CFA 200',instant:true,cashout:true,stream:false,sports:20,lic:'ARTP Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit. Orange Money and Wave. T&Cs. 18+.',pms:['Orange Money','Wave','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Senegal',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:57,lic:'ARTP Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Orange Money','Wave','MTN MoMo','Visa','Mastercard']},
{abbr:'PB',bg:'#FF4500',tc:'#fff',name:'Premier Bet Sénégal',url:'https://www.premierbet.com/sn',tag:'Licensed in Senegal – Football & More',off:'Welcome Bonus on First Deposit',top:'Deposit Bonus',stars:4,min:'CFA 200',instant:true,cashout:true,stream:false,sports:20,lic:'ARTP Licensed',nodep:false,badge:'',terms:'Welcome bonus on first deposit. Orange Money and Wave accepted. T&Cs. 18+.',pms:['Orange Money','Wave','MTN MoMo','Bank Transfer']},
{abbr:'LNS',bg:'#E65100',tc:'#fff',name:'Lonasebet',url:'https://www.lonasebet.com',tag:'Senegal Local – Ligue 1 Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:false,sports:15,lic:'ARSEL Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Orange Money. T&Cs. 18+.',pms:['Orange Money','Free Money','Wave','Visa']},
{abbr:'MJS',bg:'#880E4F',tc:'#fff',name:'Mojabet Senegal',url:'https://www.mojabet.com',tag:'Moja – One Goal, Big Wins',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'CFA 500',instant:true,cashout:true,stream:false,sports:18,lic:'ARSEL Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Orange Money. T&Cs. 18+.',pms:['Orange Money','Free Money','Wave']}
],
RW:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Rwanda',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – 50+ Sports',off:'200% First Deposit Bonus – Up to RWF 200,000',top:'RWF 200,000',stars:4,min:'RWF 500',instant:true,cashout:true,stream:true,sports:50,lic:'RGC Licensed',nodep:false,badge:'',terms:'200% match up to RWF 200,000. Wager x5. Min odds 1.40. 30 days. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Visa','Mastercard']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'BetPawa Rwanda',url:'https://www.betpawa.rw',tag:'Low-Stakes Jackpot Brand – Now in Rwanda',off:'Weekly Jackpot – Bet from RWF 200',top:'Jackpot',stars:4,min:'RWF 200',instant:true,cashout:false,stream:false,sports:20,lic:'RGC Licensed',nodep:false,badge:'new',terms:'Bet from RWF 200 on jackpot products. MTN MoMo Rwanda and Airtel Money Rwanda. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Rwanda',url:'https://www.sportpesa.rw',tag:'Jackpot Brand – RPL Coverage',off:'200% Karibu Gift on First Deposit',top:'200% Match',stars:4,min:'RWF 200',instant:true,cashout:true,stream:false,sports:20,lic:'RGC Licensed',nodep:false,badge:'',terms:'200% Karibu Gift on first deposit. MTN MoMo Rwanda. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Rwanda',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'RWF 500',instant:true,cashout:true,stream:false,sports:57,lic:'RGC Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Visa','Mastercard']},
{abbr:'BPR',bg:'#34363B',tc:'#fff',name:'BetPawa Rwanda',url:'https://www.betpawa.rw',tag:'Rwanda Jackpot – Win Big from RWF 100',off:'Weekly Jackpot from RWF 100',top:'Jackpot',stars:4,min:'RWF 100',instant:true,cashout:false,stream:false,sports:15,lic:'RRA Licensed',nodep:false,badge:'',terms:'Bet from RWF 100 on jackpots. MTN MoMo Rwanda. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer']},
{abbr:'FTR',bg:'#E65100',tc:'#fff',name:'Fortebet Rwanda',url:'https://www.fortebet.ug',tag:'Uganda Brand – Now Serving Rwanda',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'RWF 500',instant:true,cashout:true,stream:false,sports:20,lic:'RRA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer']},
{abbr:'FZR',bg:'#0288D1',tc:'#fff',name:'Forzza Rwanda',url:'https://www.forzza.com',tag:'Forzza – Multi-Market Brand',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'RWF 500',instant:true,cashout:true,stream:false,sports:18,lic:'RRA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda']},
{abbr:'GGR',bg:'#388E3C',tc:'#fff',name:'GorillaGames',url:'https://www.gorillagames.rw',tag:"Rwanda's Own – Gorilla Nation Betting",off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'RWF 500',instant:true,cashout:true,stream:false,sports:18,lic:'RRA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo Rwanda. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Bank Transfer']},
{abbr:'WNR',bg:'#1565C0',tc:'#fff',name:'Winner Rwanda',url:'https://www.winner.com',tag:'International Brand – AFCON Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'RWF 500',instant:true,cashout:true,stream:false,sports:25,lic:'RRA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Rwanda','Airtel Money Rwanda','Visa','Mastercard']}
],
ZW:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Zimbabwe',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Zimbabwe – 200%',off:'200% First Deposit Bonus – Up to $200',top:'$200',stars:4,min:'$1',instant:true,cashout:true,stream:true,sports:50,lic:'LGB Zimbabwe',nodep:false,badge:'hot',terms:'200% match up to $200. Wager x5 at min odds 1.40. 30 days. EcoCash accepted. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Zimbabwe',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to $130',top:'$130',stars:4,min:'$1',instant:true,cashout:true,stream:true,sports:40,lic:'LGB Zimbabwe',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to $130. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Zimbabwe',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to $250',top:'$250',stars:4,min:'$1',instant:true,cashout:false,stream:true,sports:150,lic:'LGB Zimbabwe',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to $250. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Zimbabwe',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'$1',instant:true,cashout:true,stream:false,sports:57,lic:'LGB Zimbabwe',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Zimbabwe',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to $200',top:'$200',stars:4,min:'$1',instant:true,cashout:true,stream:true,sports:50,lic:'LGB Zimbabwe',nodep:false,badge:'new',terms:'200% match on first deposit up to $200. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Visa','Mastercard']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Zimbabwe',url:'https://www.hollywoodbets.net',tag:'South Africa\'s Biggest Brand – In Zimbabwe',off:'$5 Free Bet on Registration',top:'$5 Free Bet',stars:5,min:'$1',instant:true,cashout:true,stream:true,sports:28,lic:'LGB Zimbabwe',nodep:true,badge:'',terms:'$5 free bet after registration and FICA. Min odds 0.5. 24-hour expiry. EcoCash accepted. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Bank Transfer','Visa']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Zimbabwe',url:'https://www.betway.co.za',tag:'International Brand – PSL & EPL',off:'50% Welcome Bonus – Up to $50',top:'$50',stars:4,min:'$1',instant:true,cashout:true,stream:true,sports:28,lic:'LGB Zimbabwe',nodep:false,badge:'',terms:'50% match up to $50. EcoCash and OneMoney. Wager 3x. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Bank Transfer','Visa']},
{abbr:'BLB',bg:'#F57F17',tc:'#111',name:'Bolabet Zimbabwe',url:'https://www.bolabet.co.zw',tag:'Local Zimbabwe Brand – PSL & Sports',off:'$5 Welcome Bonus on First Deposit',top:'$5 Bonus',stars:3,min:'$1',instant:true,cashout:false,stream:false,sports:18,lic:'LGB Zimbabwe',nodep:false,badge:'',terms:'$5 bonus on first deposit. EcoCash accepted. T&Cs. 18+.',pms:['EcoCash (Econet)','OneMoney (NetOne)','Bank Transfer']},
{abbr:'BT7',bg:'#0D47A1',tc:'#fff',name:'Bet247 Zimbabwe',url:'https://www.bet247.co.zw',tag:'Zimbabwe Sports Betting Platform',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Bank Transfer','Visa']},
{abbr:'BZB',bg:'#4527A0',tc:'#fff',name:'BezBets',url:'https://www.bezbets.com',tag:'Zimbabwe Betting – No Bez Boundaries',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Bank Transfer']},
{abbr:'LKB',bg:'#F57F17',tc:'#fff',name:'Luckybets Zimbabwe',url:'https://www.luckybets.co.zw',tag:'Lucky in Zimbabwe – Daily Big Wins',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Bank Transfer']},
{abbr:'MWO',bg:'#1B5E20',tc:'#fff',name:'MWOS',url:'https://www.mwos.co.zw',tag:'Zimbabwe Sports Specialist',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Bank Transfer']},
{abbr:'PRZ',bg:'#7B1FA2',tc:'#fff',name:'Pridebet Zimbabwe',url:'https://www.pridebet.com',tag:'Pride of Zimbabwe Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:18,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Visa','Mastercard']},
{abbr:'SPC',bg:'#00838F',tc:'#fff',name:'SpinCity Zimbabwe',url:'https://www.spincity.co.zw',tag:'SpinCity – Casino & Sports in ZW',off:'100% Bonus + Free Spins',top:'100% + Spins',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match + free spins. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Visa','Mastercard']},
{abbr:'WBK',bg:'#E65100',tc:'#fff',name:'Winbucks Zimbabwe',url:'https://www.winbucks.co.zw',tag:'Win Bucks – Zimbabwe Cash Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'BCLB Zimbabwe',nodep:false,badge:'',terms:'100% match on first deposit. EcoCash. T&Cs. 18+.',pms:['EcoCash','Telecash','Bank Transfer']}
],
MW:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Malawi',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Malawi – 200%',off:'200% First Deposit Bonus – Up to MWK 345,000',top:'MWK 345,000',stars:4,min:'MWK 200',instant:true,cashout:true,stream:true,sports:50,lic:'Malawi Gaming Board',nodep:false,badge:'hot',terms:'200% match up to MWK 345,000. Wager x5 at min odds 1.40. 30 days. Airtel Money Malawi. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Malawi',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to MWK 225,000',top:'MWK 225,000',stars:4,min:'MWK 200',instant:true,cashout:true,stream:true,sports:40,lic:'Malawi Gaming Board',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to MWK 225,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Malawi',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to MWK 430,000',top:'MWK 430,000',stars:4,min:'MWK 200',instant:true,cashout:false,stream:true,sports:150,lic:'Malawi Gaming Board',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to MWK 430,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Malawi',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'MWK 200',instant:true,cashout:true,stream:false,sports:57,lic:'Malawi Gaming Board',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Malawi',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to MWK 345,000',top:'MWK 345,000',stars:4,min:'MWK 200',instant:true,cashout:true,stream:true,sports:50,lic:'Malawi Gaming Board',nodep:false,badge:'new',terms:'200% match on first deposit up to MWK 345,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Visa','Mastercard']},
{abbr:'BT',bg:'#FCED0E',tc:'#1B3A7A',name:'Betika Malawi',url:'https://www.betika.com/en-mw/',tag:'East Africa\'s #1 – Now in Malawi',off:'Free Bet on Signup + MWK Welcome Bonus',top:'Free Bets',stars:5,min:'MWK 200',instant:true,cashout:true,stream:false,sports:20,lic:'Malawi Gaming Board',nodep:true,badge:'',terms:'Register and verify. Free bet on signup. Airtel Money Malawi. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']},
{abbr:'SP',bg:'#2F3081',tc:'#fff',name:'SportPesa Malawi',url:'https://www.sportpesa.co.mw',tag:'Jackpot & Super League Coverage',off:'200% Karibu Gift on First Deposit',top:'200% Match',stars:4,min:'MWK 200',instant:true,cashout:true,stream:false,sports:20,lic:'Malawi Gaming Board',nodep:false,badge:'',terms:'200% Karibu Gift on first deposit. Airtel Money Malawi and TNM. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Malawi',url:'https://www.hollywoodbets.net',tag:'SA\'s Biggest Brand – Expanded to Malawi',off:'MWK 2,000 Free Bet on Signup',top:'MWK 2,000 Free',stars:4,min:'MWK 200',instant:true,cashout:true,stream:false,sports:22,lic:'Malawi Gaming Board',nodep:true,badge:'',terms:'MWK 2,000 free bet on registration. Airtel Money Malawi. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']},
{abbr:'BLB',bg:'#F57F17',tc:'#111',name:'Bolabet Malawi',url:'https://www.bolabet.co.mw',tag:'Local Malawi Brand – Super League Coverage',off:'MWK 5,000 Welcome Bonus on First Deposit',top:'MWK 5,000',stars:3,min:'MWK 200',instant:true,cashout:false,stream:false,sports:18,lic:'Malawi Gaming Board',nodep:false,badge:'',terms:'MWK 5,000 bonus on first deposit. Airtel Money Malawi. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']},
{abbr:'BPM',bg:'#34363B',tc:'#fff',name:'BetPawa Malawi',url:'https://www.betpawa.mw',tag:'Malawi Jackpot from MK 500',off:'Weekly Jackpot from MK 500',top:'Jackpot',stars:4,min:'MK 500',instant:true,cashout:false,stream:false,sports:15,lic:'MGA Licensed',nodep:false,badge:'',terms:'Bet from MK 500 on jackpots. Airtel Money. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']},
{abbr:'MMG',bg:'#1565C0',tc:'#fff',name:'MMG Malawi',url:'https://www.mmg.mw',tag:'Malawi Local Brand – Full Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MK 500',instant:true,cashout:true,stream:false,sports:18,lic:'MGA Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Airtel Money. T&Cs. 18+.',pms:['Airtel Money Malawi','TNM Mpamba','Bank Transfer']}
],
MZ:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Mozambique',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Mozambique – 200%',off:'200% First Deposit Bonus – Up to MZN 12,800',top:'MZN 12,800',stars:4,min:'MZN 50',instant:true,cashout:true,stream:true,sports:50,lic:'IGA Licensed',nodep:false,badge:'hot',terms:'200% match up to MZN 12,800. Wager x5 at min odds 1.40. 30 days. M-Pesa Mozambique. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Mozambique',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to MZN 8,300',top:'MZN 8,300',stars:4,min:'MZN 50',instant:true,cashout:true,stream:true,sports:40,lic:'IGA Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to MZN 8,300. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Mozambique',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to MZN 16,000',top:'MZN 16,000',stars:4,min:'MZN 50',instant:true,cashout:false,stream:true,sports:150,lic:'IGA Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to MZN 16,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Mozambique',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'MZN 50',instant:true,cashout:true,stream:false,sports:57,lic:'IGA Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Mozambique',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to MZN 12,800',top:'MZN 12,800',stars:4,min:'MZN 50',instant:true,cashout:true,stream:true,sports:50,lic:'IGA Licensed',nodep:false,badge:'new',terms:'200% match on first deposit up to MZN 12,800. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Visa','Mastercard']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Mozambique',url:'https://www.hollywoodbets.net',tag:'Largest African Bookmaker – Now in MZ',off:'MZN 150 Free Bet on Registration',top:'MZN 150 Free',stars:5,min:'MZN 10',instant:true,cashout:true,stream:true,sports:28,lic:'IGA Licensed',nodep:true,badge:'',terms:'MZN 150 free bet after registration + ID verification. M-Pesa Mozambique. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Bank Transfer','Visa']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Mozambique',url:'https://www.betway.co.mz',tag:'International Brand – EPL & Moçambola',off:'50% Welcome Bonus – Up to MZN 3,000',top:'MZN 3,000',stars:4,min:'MZN 50',instant:true,cashout:true,stream:true,sports:28,lic:'IGA Licensed',nodep:false,badge:'',terms:'50% match up to MZN 3,000. M-Pesa Mozambique. Wager 3x. T&Cs. 18+.',pms:['M-Pesa Mozambique','e-Mola','Bank Transfer','Visa']},
{abbr:'888M',bg:'#1A237E',tc:'#fff',name:'888Bet Mozambique',url:'https://www.888bet.co.mz',tag:'888 – Premium Odds for Mozambique',off:'100% Welcome Bonus – Up to MT 5,000',top:'MT 5,000',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:20,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match up to MT 5,000. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer','Visa']},
{abbr:'BAR',bg:'#145A8C',tc:'#fff',name:'BetArena Mozambique',url:'https://www.betarena.co.mz',tag:'Mozambique Sports Arena',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:18,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer']},
{abbr:'BYM',bg:'#00695C',tc:'#fff',name:'BetYetu Mozambique',url:'https://www.betyetu.co.mz',tag:'BetYetu – Mozambique Local Brand',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:15,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer']},
{abbr:'ELM',bg:'#4CAF50',tc:'#fff',name:'ElephantBet Mozambique',url:'https://www.elephantbet.com',tag:'Elephant – Big Odds in Mozambique',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:18,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Visa','Mastercard']},
{abbr:'BTU',bg:'#880E4F',tc:'#fff',name:'BantuBet Mozambique',url:'https://www.bantubet.co.mz',tag:'Bantu – African Spirit Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:15,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer']},
{abbr:'JGB',bg:'#1565C0',tc:'#fff',name:'Jogabets',url:'https://www.jogabets.co.mz',tag:'Joga – Play & Win in Mozambique',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:15,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer']},
{abbr:'OLM',bg:'#00838F',tc:'#fff',name:'Olabet Mozambique',url:'https://www.olabet.co.mz',tag:'Ola – Friendly Mozambique Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:15,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer']},
{abbr:'PLC',bg:'#0D47A1',tc:'#fff',name:'Placard Mozambique',url:'https://www.placard.co.mz',tag:'Placard – Mozambique Official Operator',off:'100% Welcome Bonus',top:'100% Match',stars:4,min:'MT 50',instant:true,cashout:true,stream:false,sports:20,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Bank Transfer','Visa']},
{abbr:'SPC',bg:'#00838F',tc:'#fff',name:'SpinCity Mozambique',url:'https://www.spincity.co.mz',tag:'SpinCity – Casino & Sports MZ',off:'100% Bonus + Free Spins',top:'100% + Spins',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:15,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match + free spins. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Visa']},
{abbr:'WNM',bg:'#1565C0',tc:'#fff',name:'Winner Mozambique',url:'https://www.winner.com',tag:'International Brand – AFCON Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'MT 50',instant:true,cashout:true,stream:false,sports:25,lic:'INAR Licensed',nodep:false,badge:'',terms:'100% match on first deposit. M-Pesa. T&Cs. 18+.',pms:['M-Pesa','e-Mola','Visa','Mastercard']}
],
AO:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Angola',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Angola\'s Biggest Online Bookmaker',off:'200% First Deposit Bonus – Up to AOA 80,000',top:'AOA 80,000',stars:5,min:'AOA 500',instant:true,cashout:true,stream:true,sports:50,lic:'ID Angola',nodep:false,badge:'hot',terms:'200% match up to AOA 80,000. Bank transfer and Visa accepted. Wager x5. 30 days. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Angola',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to AOA 160,000',top:'AOA 160,000',stars:4,min:'AOA 500',instant:true,cashout:false,stream:true,sports:150,lic:'ID Angola',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to AOA 160,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'888A',bg:'#1A237E',tc:'#fff',name:'888Bet Angola',url:'https://www.888bet.ao',tag:'888 – Angola Premium Odds',off:'100% Welcome Bonus – Up to Kz 5,000',top:'Kz 5,000',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:20,lic:'ID Angola',nodep:false,badge:'',terms:'100% match up to Kz 5,000. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Angola',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'AOA 500',instant:true,cashout:true,stream:false,sports:57,lic:'ID Angola',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'BTU',bg:'#880E4F',tc:'#fff',name:'BantuBet Angola',url:'https://www.bantubet.co.ao',tag:'Bantu – African Spirit Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:15,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa']},
{abbr:'EBA',bg:'#0D47A1',tc:'#fff',name:'eBet Angola',url:'https://www.ebet.ao',tag:'eBet – Angola & SA Multi-Market',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:18,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'ELA',bg:'#4CAF50',tc:'#fff',name:'ElephantBet Angola',url:'https://www.elephantbet.com',tag:'Elephant – Big Odds in Angola',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:18,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'GDB',bg:'#F9A825',tc:'#111',name:'Goldenbet Angola',url:'https://www.goldenbet.ao',tag:'Golden Odds – Angola Premier League',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:15,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa']},
{abbr:'KWZ',bg:'#B71C1C',tc:'#fff',name:'Kwanzabet',url:'https://www.kwanzabet.com',tag:"Angola's Currency of Wins",off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:true,stream:false,sports:15,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa']},
{abbr:'PBA',bg:'#FF4500',tc:'#fff',name:'Premierbet Angola',url:'https://www.premierbet.com',tag:'20+ African Markets – Angola',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'Kz 100',instant:true,cashout:false,stream:false,sports:18,lic:'ID Angola',nodep:false,badge:'',terms:'100% match on first deposit. Bank Transfer. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']}
],
CD:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet DRC',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'DRC\'s Largest Online Bookmaker',off:'200% First Deposit Bonus – Up to CDF 200,000',top:'CDF 200,000',stars:5,min:'CDF 1,000',instant:true,cashout:true,stream:true,sports:50,lic:'ARJ DRC',nodep:false,badge:'hot',terms:'200% match up to CDF 200,000. M-Pesa DRC and Airtel Money DRC. Wager x5. 30 days. T&Cs. 18+.',pms:['M-Pesa DRC (Vodacom)','Airtel Money DRC','Orange Money','Bank Transfer']},
{abbr:'BPW',bg:'#34363B',tc:'#fff',name:'BetPawa DRC',url:'https://www.betpawa.cd',tag:'Africa\'s #1 Low-Stakes Brand – Now in DRC',off:'Weekly Jackpot – Bet from CDF 500',top:'Jackpot CDF 500',stars:4,min:'CDF 500',instant:true,cashout:false,stream:false,sports:20,lic:'ARJ DRC',nodep:false,badge:'new',terms:'Bet from CDF 500 on jackpot products. Mobile money accepted. T&Cs. 18+.',pms:['M-Pesa DRC (Vodacom)','Airtel Money DRC','Orange Money','Bank Transfer']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari DR Congo',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'CDF 1,000',instant:true,cashout:true,stream:false,sports:57,lic:'ARJ DRC',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['M-Pesa DRC (Vodacom)','Airtel Money DRC','Orange Money','Bank Transfer']}
],
BW:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Botswana',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Botswana – 200%',off:'200% First Deposit Bonus – Up to BWP 2,700',top:'BWP 2,700',stars:4,min:'BWP 5',instant:true,cashout:true,stream:true,sports:50,lic:'GAB Licensed',nodep:false,badge:'hot',terms:'200% match up to BWP 2,700. Wager x5 at min odds 1.40. 30 days. FNB Botswana. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Botswana',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to BWP 1,750',top:'BWP 1,750',stars:4,min:'BWP 5',instant:true,cashout:true,stream:true,sports:40,lic:'GAB Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to BWP 1,750. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Botswana',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to BWP 3,400',top:'BWP 3,400',stars:4,min:'BWP 5',instant:true,cashout:false,stream:true,sports:150,lic:'GAB Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to BWP 3,400. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Botswana',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'BWP 5',instant:true,cashout:true,stream:false,sports:57,lic:'GAB Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Botswana',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to BWP 2,700',top:'BWP 2,700',stars:4,min:'BWP 5',instant:true,cashout:true,stream:true,sports:50,lic:'GAB Licensed',nodep:false,badge:'new',terms:'200% match on first deposit up to BWP 2,700. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Visa','Mastercard']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Botswana',url:'https://www.hollywoodbets.net',tag:'Africa\'s Largest Retail Bookmaker',off:'BWP 25 Free Bet on Registration',top:'BWP 25 Free',stars:5,min:'BWP 2',instant:true,cashout:true,stream:true,sports:28,lic:'GAB Licensed',nodep:true,badge:'',terms:'BWP 25 free bet after registration. FNB Botswana and Orange Money. Min odds 0.5. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Bank Transfer','Visa']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Botswana',url:'https://www.betway.co.bw',tag:'International Brand – PSL & EPL',off:'50% Welcome Bonus – Up to BWP 500',top:'BWP 500',stars:4,min:'BWP 5',instant:true,cashout:true,stream:true,sports:28,lic:'GAB Licensed',nodep:false,badge:'',terms:'50% match up to BWP 500. FNB Botswana. Wager 3x. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Bank Transfer','Visa']},
{abbr:'SUP',bg:'#63FD8C',tc:'#111',name:'Supabets Botswana',url:'https://www.supabets.com',tag:'SA Brand – Now in Botswana',off:'100% Welcome Bonus – Up to BWP 1,000',top:'BWP 1,000',stars:4,min:'BWP 5',instant:true,cashout:true,stream:false,sports:25,lic:'GAB Licensed',nodep:false,badge:'',terms:'100% match on first deposit up to BWP 1,000. Wagering requirements apply. T&Cs. 18+.',pms:['FNB Botswana','Orange Money Botswana','Bank Transfer','Visa','Mastercard']},
{abbr:'BBW',bg:'#4527A0',tc:'#fff',name:'BBets Botswana',url:'https://www.bbets.co.bw',tag:'Botswana Local Brand – BPL Coverage',off:'100% Welcome Bonus – Up to P 500',top:'P 500',stars:3,min:'P 5',instant:true,cashout:true,stream:false,sports:15,lic:'GCB Licensed',nodep:false,badge:'',terms:'100% match up to P 500. Orange Botswana. T&Cs. 18+.',pms:['Orange Botswana','Standard Chartered','Bank Transfer','Visa']},
{abbr:'BT7',bg:'#0D47A1',tc:'#fff',name:'Bet267 Botswana',url:'https://www.bet267.co.bw',tag:'267 – Botswana Area Code Betting',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'P 5',instant:true,cashout:true,stream:false,sports:15,lic:'GCB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Orange Botswana. T&Cs. 18+.',pms:['Orange Botswana','Standard Chartered','Bank Transfer']},
{abbr:'BXP',bg:'#FF6F00',tc:'#fff',name:'BetXplosion Botswana',url:'https://www.betxplosion.co.bw',tag:'Explosive Odds in Botswana',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'P 5',instant:true,cashout:true,stream:false,sports:15,lic:'GCB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Orange Botswana','Bank Transfer','Visa']},
{abbr:'PST',bg:'#37474F',tc:'#fff',name:'PSTBet Botswana',url:'https://www.pstbet.co.bw',tag:'PST – BW & NA Multi-Market',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'P 5',instant:true,cashout:true,stream:false,sports:18,lic:'GCB Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Orange Botswana','Standard Chartered','Bank Transfer','Visa']}
],
EG:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Egypt',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Egypt – 200%',off:'200% First Deposit Bonus – Up to EGP 20,000',top:'EGP 20,000',stars:5,min:'EGP 10',instant:true,cashout:true,stream:true,sports:50,lic:'Curacao Licensed',nodep:false,badge:'hot',terms:'200% match up to EGP 20,000. Wager x5 at min odds 1.40. 30 days. Vodafone Cash EG. T&Cs. 18+.',pms:['Vodafone Cash Egypt','Bank Transfer','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Egypt',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to EGP 30,000',top:'EGP 30,000',stars:4,min:'EGP 10',instant:true,cashout:false,stream:true,sports:150,lic:'Curacao Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to EGP 30,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Vodafone Cash Egypt','Orange Money Egypt','Bank Transfer','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Egypt',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – Egyptian Premier League Coverage',off:'200% First Deposit Bonus – Up to EGP 15,000',top:'EGP 15,000',stars:4,min:'EGP 10',instant:true,cashout:true,stream:true,sports:40,lic:'Curacao Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to EGP 15,000. Wager x5. 30 days. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Egypt',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'EGP 10',instant:true,cashout:true,stream:false,sports:57,lic:'Curacao Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Vodafone Cash Egypt','Bank Transfer','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Egypt',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – CAF & EPL Coverage',off:'200% First Deposit Bonus – Up to EGP 12,000',top:'EGP 12,000',stars:4,min:'EGP 10',instant:true,cashout:true,stream:true,sports:50,lic:'Curacao Licensed',nodep:false,badge:'new',terms:'200% match up to EGP 12,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Vodafone Cash Egypt','Bank Transfer','Visa','Mastercard']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Egypt',url:'https://www.betway.com',tag:'International Brand – Salah Specials',off:'100% Welcome Bonus – Up to EGP 5,000',top:'EGP 5,000',stars:4,min:'EGP 20',instant:true,cashout:true,stream:true,sports:28,lic:'Curacao Licensed',nodep:false,badge:'',terms:'100% match up to EGP 5,000. Wager 5x. 30 days. T&Cs. 18+.',pms:['Bank Transfer','Visa','Mastercard']}
],
MA:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Maroc',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'200% Bonus – Botola Pro & La Liga',off:'200% First Deposit Bonus – Up to MAD 4,000',top:'MAD 4,000',stars:4,min:'MAD 10',instant:true,cashout:true,stream:true,sports:50,lic:'Curacao Licensed',nodep:false,badge:'',terms:'200% match up to MAD 4,000. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Bank Transfer','CIH Bank','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Maroc',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to MAD 5,000',top:'MAD 5,000',stars:4,min:'MAD 10',instant:true,cashout:false,stream:true,sports:150,lic:'Curacao Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to MAD 5,000. Wager x5. 30 days. T&Cs. 18+.',pms:['Bank Transfer','CIH Bank','Attijari Bank','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Maroc',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports + WC 2026',off:'200% First Deposit Bonus – Up to MAD 3,500',top:'MAD 3,500',stars:4,min:'MAD 10',instant:true,cashout:true,stream:true,sports:40,lic:'Curacao Licensed',nodep:false,badge:'new',terms:'Code WBONUS1. 200% match up to MAD 3,500. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Bank Transfer','CIH Bank','Orange Money Morocco','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Morocco',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'MAD 10',instant:true,cashout:true,stream:false,sports:57,lic:'Curacao Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Bank Transfer','CIH Bank','Visa','Mastercard']},
{abbr:'PMU',bg:'#003580',tc:'#fff',name:'PMU Maroc',url:'https://www.pmu.ma',tag:'State-Licensed Operator – Morocco Official',off:'Bonus de Bienvenue – Premier Dépôt',top:'MAD 500',stars:5,min:'MAD 10',instant:true,cashout:true,stream:false,sports:20,lic:'MDJS Licensed',nodep:false,badge:'hot',terms:'Bonus de bienvenue sur premier dépôt. CIH Bank et Attijari Bank. T&Cs. 18+.',pms:['CIH Bank','Attijari Bank','Orange Money Morocco','Bank Transfer','Visa']}
],
NA:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Namibia',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Namibia – 200%',off:'200% First Deposit Bonus – Up to NAD 3,600',top:'NAD 3,600',stars:4,min:'NAD 5',instant:true,cashout:true,stream:true,sports:50,lic:'GBN Licensed',nodep:false,badge:'hot',terms:'200% match up to NAD 3,600. Wager x5 at min odds 1.40. 30 days. FNB Namibia. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Visa','Mastercard']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Namibia',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – Up to NAD 2,340',top:'NAD 2,340',stars:4,min:'NAD 5',instant:true,cashout:true,stream:true,sports:40,lic:'GBN Licensed',nodep:false,badge:'',terms:'Code WBONUS1. 200% match up to NAD 2,340. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Visa','Mastercard']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Namibia',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to NAD 4,500',top:'NAD 4,500',stars:4,min:'NAD 5',instant:true,cashout:false,stream:true,sports:150,lic:'GBN Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match up to NAD 4,500. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Visa','Mastercard']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Namibia',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'NAD 5',instant:true,cashout:true,stream:false,sports:57,lic:'GBN Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Visa','Mastercard']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Namibia',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus – Up to NAD 3,600',top:'NAD 3,600',stars:4,min:'NAD 5',instant:true,cashout:true,stream:true,sports:50,lic:'GBN Licensed',nodep:false,badge:'new',terms:'200% match on first deposit up to NAD 3,600. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Visa','Mastercard']},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Namibia',url:'https://www.hollywoodbets.net',tag:'SA\'s Largest – Strong Namibian Presence',off:'NAD 25 Free Bet on Registration',top:'NAD 25 Free',stars:5,min:'NAD 2',instant:true,cashout:true,stream:true,sports:28,lic:'GBN Licensed',nodep:true,badge:'',terms:'NAD 25 free bet after registration. FNB Namibia and Standard Bank Namibia. Min odds 0.5. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Bank Windhoek','Bank Transfer','Visa']},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Namibia',url:'https://www.betway.com',tag:'International Brand – NFA League',off:'50% Welcome Bonus – Up to NAD 1,000',top:'NAD 1,000',stars:4,min:'NAD 5',instant:true,cashout:true,stream:true,sports:28,lic:'GBN Licensed',nodep:false,badge:'',terms:'50% match up to NAD 1,000. FNB Namibia. Wager 3x. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Bank Transfer','Visa']},
{abbr:'SPB',bg:'#076da7',tc:'#fff',name:'Sportingbet Namibia',url:'https://www.sportingbet.co.za',tag:'International Brand – Cricket & Rugby',off:'100% Welcome Bonus – Up to NAD 500',top:'NAD 500',stars:3,min:'NAD 10',instant:true,cashout:true,stream:false,sports:22,lic:'GBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit up to NAD 500. Bank transfer. T&Cs. 18+.',pms:['FNB Namibia','Standard Bank Namibia','Bank Transfer','Visa']},
{abbr:'ALB',bg:'#1565C0',tc:'#fff',name:'Allbet Namibia',url:'https://www.allbet.com.na',tag:'Allbet – Namibia Sports Coverage',off:'100% Welcome Bonus – Up to N$500',top:'N$500',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match up to N$500. Bank Windhoek. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Nedbank Namibia','Visa']},
{abbr:'CSB',bg:'#795548',tc:'#fff',name:'Castlebet Namibia',url:'https://www.castlebet.com.na',tag:'Castle Strong Odds in Namibia',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. Bank Windhoek. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Visa']},
{abbr:'CLN',bg:'#37474F',tc:'#fff',name:'Classic Namibia',url:'https://www.classic.com.na',tag:'Classic – Traditional Namibia Betting',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Nedbank Namibia','Visa']},
{abbr:'FZN',bg:'#0288D1',tc:'#fff',name:'Forzza Namibia',url:'https://www.forzza.com',tag:'Forzza – NA & Rwanda Multi-Market',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:18,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Bank Windhoek','Nedbank Namibia','Visa','Mastercard']},
{abbr:'LBN',bg:'#F9A825',tc:'#111',name:'Luckybet Namibia',url:'https://www.luckybet.com.na',tag:'Lucky in Namibia – Daily Big Wins',off:'100% First Deposit Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Visa']},
{abbr:'PSN',bg:'#37474F',tc:'#fff',name:'PSTBet Namibia',url:'https://www.pstbet.co.bw',tag:'PST – BW & NA Multi-Market',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:18,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Nedbank Namibia','Visa']},
{abbr:'SPC',bg:'#00838F',tc:'#fff',name:'SpinCity Namibia',url:'https://www.spincity.com',tag:'SpinCity – Casino & Sports NA',off:'100% Bonus + Free Spins',top:'100% + Spins',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match + free spins. T&Cs. 18+.',pms:['Bank Windhoek','Nedbank Namibia','Visa','Mastercard']},
{abbr:'SUP',bg:'#1A237E',tc:'#fff',name:'Supremebet Namibia',url:'https://www.supremebet.com.na',tag:'Supreme Odds – Namibia Premier League',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'N$10',instant:true,cashout:true,stream:false,sports:15,lic:'RFBN Licensed',nodep:false,badge:'',terms:'100% match on first deposit. T&Cs. 18+.',pms:['Bank Windhoek','Standard Bank Namibia','Nedbank Namibia','Visa']}
],
SL:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Sierra Leone',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Sierra Leone',off:'200% First Deposit Bonus – Up to Le 2,000,000',top:'Le 2,000,000',stars:4,min:'Le 1,000',instant:true,cashout:true,stream:true,sports:50,lic:'NLA Licensed',nodep:false,badge:'hot',terms:'200% match. Orange Money SL. Wager x5. 30 days. T&Cs. 18+.',pms:['Orange Money Sierra Leone','Africell Money','Bank Transfer','Visa']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Sierra Leone',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – Up to Le 1,500,000',top:'Le 1,500,000',stars:4,min:'Le 1,000',instant:true,cashout:false,stream:true,sports:150,lic:'NLA Licensed',nodep:false,badge:'',terms:'Code MBMAX. 200% match. Wager x5. 30 days. T&Cs. 18+.',pms:['Orange Money Sierra Leone','Africell Money','Bank Transfer','Visa']},
{abbr:'PP',bg:'#172BE2',tc:'#fff',name:'Paripesa Sierra Leone',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',tag:'200% Bonus – 50+ Sports Markets',off:'200% First Deposit Bonus',top:'200% Match',stars:4,min:'Le 1,000',instant:true,cashout:true,stream:true,sports:50,lic:'NLA Licensed',nodep:false,badge:'new',terms:'200% match. Orange Money SL. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Orange Money Sierra Leone','Bank Transfer','Visa']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Sierra Leone',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'Le 1,000',instant:true,cashout:true,stream:false,sports:57,lic:'NLA Licensed',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Orange Money Sierra Leone','Africell Money','Bank Transfer','Visa']}
],
LR:[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Liberia',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'Highest Bonus in Liberia',off:'200% First Deposit Bonus – USD',top:'$200 Match',stars:4,min:'$2',instant:true,cashout:true,stream:true,sports:50,lic:'National Lottery',nodep:false,badge:'hot',terms:'200% match. Lonestar MTN MoMo. Wager x5. 30 days. T&Cs. 18+.',pms:['Lonestar MTN Mobile Money','Orange Liberia','Bank Transfer','Visa']},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Liberia',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'200% Bonus – 150+ Sports Markets',off:'200% First Deposit Bonus – USD',top:'$150 Match',stars:4,min:'$2',instant:true,cashout:false,stream:true,sports:150,lic:'National Lottery',nodep:false,badge:'',terms:'Code MBMAX. 200% match. Wager x5 at min odds 1.40. 30 days. T&Cs. 18+.',pms:['Lonestar MTN Mobile Money','Bank Transfer','Visa']},
{abbr:'BN',bg:'#009277',tc:'#fff',name:'BetWinner Liberia',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',tag:'200% Bonus – 40+ Sports Markets',off:'200% First Deposit Bonus – USD',top:'$100 Match',stars:4,min:'$2',instant:true,cashout:true,stream:true,sports:40,lic:'National Lottery',nodep:false,badge:'new',terms:'Code WBONUS1. 200% match. Wager x5. 30 days. T&Cs. 18+.',pms:['Lonestar MTN Mobile Money','Orange Liberia','Bank Transfer','Visa']},
{abbr:'FP',bg:'#1677FF',tc:'#fff',name:'FairPari Liberia',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',tag:'63+ Sports – 4,000+ Casino Games – Wide Payment Options',off:'100% First Deposit Bonus – Up to €100',top:'€100',stars:4,min:'$2',instant:true,cashout:true,stream:false,sports:57,lic:'National Lottery',nodep:false,badge:'hot',terms:'100% match on first deposit up to €100. Wagering requirements apply. Not valid for crypto deposits. T&Cs. 18+.',pms:['Lonestar MTN Mobile Money','Orange Liberia','Bank Transfer','Visa']},
{abbr:'DXB',bg:'#1565C0',tc:'#fff',name:'Doxxbet Liberia',url:'https://www.doxxbet.com',tag:'Doxx – European Brand in Liberia',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:18,lic:'NLC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Liberia','Orange Money','Bank Transfer','Visa']},
{abbr:'MCB',bg:'#E65100',tc:'#fff',name:'Mercurybet Liberia',url:'https://www.mercurybet.com',tag:'Mercury Fast – Liberia Sports',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'NLC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Liberia','Orange Money','Bank Transfer']},
{abbr:'STB',bg:'#FBC02D',tc:'#111',name:'Starbet Liberia',url:'https://www.starbet.com.lr',tag:'Star Bets – Shine in Liberia',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:15,lic:'NLC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Liberia','Orange Money','Bank Transfer']},
{abbr:'WNL',bg:'#1565C0',tc:'#fff',name:'Winner Liberia',url:'https://www.winner.com',tag:'International – AFCON & EPL Coverage',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:25,lic:'NLC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Liberia','Orange Money','Visa','Mastercard']},
{abbr:'BTL',bg:'#880E4F',tc:'#fff',name:'Bettomax Liberia',url:'https://www.bettomax.com',tag:'West Africa Multi-Market Brand',off:'100% Welcome Bonus',top:'100% Match',stars:3,min:'$1',instant:true,cashout:true,stream:false,sports:18,lic:'NLC Licensed',nodep:false,badge:'',terms:'100% match on first deposit. MTN MoMo. T&Cs. 18+.',pms:['MTN MoMo Liberia','Orange Money','Bank Transfer']}
]
};

// ── CASINOS ─────────────────────────────────────────────────────────────────────
// Affiliate-tracked brands first (STANDING RULE — Brands With a Real Affiliate
// Link Are Always Top-of-List + Featured, CLAUDE.md), then organic listings —
// preserve each group's relative order, don't re-rank within a group.
const CASINOS=[
{abbr:'1X',bg:'#276AA5',tc:'#fff',name:'1xBet Casino',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',tag:'3,000+ Slots – Live Dealers – Africa-Wide',off:'200% Casino Welcome Bonus',top:'200% Match',stars:4,min:'₦100',live:true,jackpot:true,slots:true,nodep:false,badge:'',terms:'200% match on first casino deposit. Wager x35. 30 days. 18+.'},
{abbr:'MB',bg:'#212121',tc:'#fff',name:'Melbet Casino',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',tag:'2,000+ Games – Mobile-First Casino',off:'100% Casino Bonus – Up to $200',top:'$200',stars:4,min:'₦100',live:true,jackpot:true,slots:true,nodep:false,badge:'',terms:'100% match on first casino deposit. Wager x35. 30 days. T&Cs. 18+.'},
{abbr:'HW',bg:'#4F2F7B',tc:'#fff',name:'Hollywoodbets Casino',url:'https://www.hollywoodbets.net',tag:'SA\'s Biggest – Slots, Live Casino & More',off:'50 Free Spins on Signup + R500 Deposit Match',top:'R500 + 50 Spins',stars:5,min:'R10',live:true,jackpot:true,slots:true,nodep:true,badge:'hot',terms:'50 free spins on registration. 100% match up to R500 on first deposit. Wager 5x. FICA required. 18+.'},
{abbr:'SUP',bg:'#63FD8C',tc:'#111',name:'Supabets Casino',url:'https://www.supabets.com',tag:'R5,000 Casino Match + 100 Free Spins',off:'100% Casino Match Up to R5,000 + 100 Spins',top:'R5,000',stars:5,min:'R10',live:true,jackpot:true,slots:true,nodep:true,badge:'hot',terms:'100% match up to R5,000 + 100 spins. Wager 3x at min odds 2.0. 15 days. 18+.'},
{abbr:'BW',bg:'#232323',tc:'#fff',name:'Betway Casino',url:'https://www.betway.com',tag:'Live Casino + Jackpot Games Across Africa',off:'100% Match Up to R3,000 + 50 Free Spins',top:'R3,000',stars:5,min:'R5',live:true,jackpot:true,slots:true,nodep:false,badge:'',terms:'100% match up to R3,000. 50 spins on Mega Moolah. Wager 25x on bonus. 30 days. 18+.'},
{abbr:'SUN',bg:'#001435',tc:'#FFAB09',name:'Sunbet Casino',url:'https://www.sunbet.co.za',tag:'Sun International – Premium Live Casino',off:'R300 Casino Free Bet + Live Table Games',top:'R300 Free',stars:4,min:'R10',live:true,jackpot:false,slots:true,nodep:true,badge:'new',terms:'R300 free bet on registration. Live tables, slots, and more. FICA required. T&Cs. 18+.'},
{abbr:'10B',bg:'#1A1A1A',tc:'#FFD700',name:'10bet Casino',url:'https://www.10bet.co.za',tag:'WCGRB Licensed Casino – Premium Experience',off:'100% Casino Deposit Match – Up to R2,000',top:'R2,000',stars:4,min:'R20',live:true,jackpot:true,slots:true,nodep:false,badge:'',terms:'100% match up to R2,000. Wager 30x. FICA required. T&Cs. 18+.'},
{abbr:'22',bg:'#024147',tc:'#fff',name:'22Bet Casino',url:'https://22bet.com',tag:'Aviator + Slots + Live Casino',off:'100% Welcome Casino Bonus',top:'100% Match',stars:3,min:'₦100',live:true,jackpot:false,slots:true,nodep:false,badge:'',terms:'100% match on first casino deposit. Wager x35. 30 days. T&Cs. 18+.'}
];

// ── SUPABASE ──────────────────────────────────────────────────────────────────
const SB_URL='https://kedfcmgqjxwzebhoeosi.supabase.co';
const SB_ANON='sb_publishable_NK9TgE3pEvmJbQ-ZmEvSjQ_22adueMj';
const _SB_HDR={apikey:SB_ANON,Authorization:'Bearer '+SB_ANON};

function _sbFetch(url,timeout=4000){
  const ctrl=new AbortController();
  const id=setTimeout(()=>ctrl.abort(),timeout);
  return fetch(url,{headers:_SB_HDR,signal:ctrl.signal}).finally(()=>clearTimeout(id));
}

async function fetchSBTips(){
  try{
    const r=await _sbFetch(`${SB_URL}/rest/v1/tips?status=eq.active&order=sort_order.asc,conf.desc`);
    if(!r.ok)return null;
    const rows=await r.json();
    if(!Array.isArray(rows)||!rows.length)return null;
    // Reject stale Supabase data: require at least one row with a specific date
    // like "8 Jun 2026". Rows using relative labels ("Today","Tomorrow","In X days")
    // were set weeks ago and re-anchor to today, surfacing played matches.
    const hasSpecificDate=rows.some(r=>/\d{1,2}\s+[A-Za-z]{3}\s+\d{4}/.test(r.date_label||''));
    if(!hasSpecificDate)return null;
    return rows.map(r=>({
      league:r.league,key:r.sport_key,match:r.match,pred:r.pred,
      analysis:r.analysis,odds:r.odds,via:r.via,conf:r.conf,
      time:r.time_disp,date:r.date_label,isAI:r.is_ai||false
    }));
  }catch(_){return null;}
}

async function fetchSBNews(){
  try{
    const r=await _sbFetch(`${SB_URL}/rest/v1/news_items?order=sort_order.asc,created_at.desc&limit=6`);
    if(!r.ok)return null;
    const rows=await r.json();
    if(!Array.isArray(rows)||!rows.length)return null;
    return rows.map(r=>({cat:r.cat,color:r.color,title:r.title,date:r.date_label}));
  }catch(_){return null;}
}

// ── DATE LABELS (must be declared before TIPS and ODDS_DATA which reference them) ─
const T_TODAY=SHORT_DATE;
const T_TMR=new Date(NOW.getTime()+  86400000).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const T_IN2 =new Date(NOW.getTime()+2*86400000).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const T_IN3 =new Date(NOW.getTime()+3*86400000).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const T_IN4 =new Date(NOW.getTime()+4*86400000).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const T_IN5 =new Date(NOW.getTime()+5*86400000).toLocaleDateString('en-GB',{day:'numeric',month:'short'});

// ── TIPS ──────────────────────────────────────────────────────────────────────
const TIPS=[
// ── Football · 8 Jun 2026 (Today) — BBC Sport confirmed ──
{league:'International Friendly',key:'world',match:'Mauritania vs Niger',pred:'Over 1.5 Goals',analysis:'Both sides have been prolific in recent CAF qualifying rounds. Mauritania, playing at home, have scored in 5 of their last 6 internationals. Niger have conceded in their last 4 away games. Expect goals in this West African friendly.',odds:'1.75',via:'Bet9ja',conf:68,time:'20:00 UTC',date:'8 Jun 2026',isAI:false},
{league:'Women\'s International Friendly',key:'afcon',match:'Senegal vs Nigeria',pred:'Both Teams to Score',analysis:'Two of the continent\'s strongest women\'s national teams meet in a pre-tournament friendly. Nigeria\'s Super Falcons are the most decorated in AFCON history (11 titles). Senegal have improved dramatically under their new coaching staff — BTTS in a close, competitive friendly.',odds:'1.90',via:'1xBet',conf:65,time:'16:00 UTC',date:'8 Jun 2026',isAI:false},
{league:'Women\'s International Friendly',key:'afcon',match:'Egypt vs Tunisia',pred:'Egypt Win or Draw',analysis:'Egypt\'s women\'s team are the dominant force in North African football. Tunisia will be competitive but Egypt\'s home advantage and superior squad depth make them clear favourites. Double chance at strong value.',odds:'1.75',via:'22Bet',conf:66,time:'17:00 UTC',date:'8 Jun 2026',isAI:false},
// ── Football · 9 Jun 2026 ──
{league:'CAF Champions League · Final',key:'cafl',match:'Mamelodi Sundowns vs Al Ahly',pred:'Over 2.5 Goals',analysis:'The CAF CL Final between Africa\'s two most dominant clubs. Sundowns\' fast transitions and Al Ahly\'s clinical finishing have combined for high-scoring encounters — both sides have scored in 8 of their last 9 CAF knockout ties.',odds:'1.85',via:'Betway',conf:72,time:'20:00 UTC',date:'9 Jun 2026',isAI:false},
{league:'AFCON 2027 Qualifier',key:'afcon',match:'Nigeria vs Rwanda',pred:'Nigeria Win & Over 1.5',analysis:'Super Eagles at home have won 11 of their last 12 qualifying games. Rwanda have conceded 2+ goals in 4 of their last 5 away qualifiers. With Osimhen leading the line, a commanding home win is expected.',odds:'1.65',via:'Bet9ja',conf:80,time:'16:00 UTC',date:'9 Jun 2026',isAI:false},
// ── Football · 10 Jun 2026 — BBC Sport confirmed ──
{league:'International Friendly',key:'world',match:'Portugal vs Nigeria',pred:'Nigeria to Score',analysis:'Nigeria\'s Super Eagles face Portugal in a high-profile pre-World Cup friendly. Victor Osimhen, Ademola Lookman and Samuel Chukwueze are in devastating form. Nigeria have scored in 8 of their last 10 internationals — back the Eagles to find the net against a Portuguese side with one eye on the World Cup.',odds:'1.85',via:'Bet9ja',conf:70,time:'20:45 UTC',date:'10 Jun 2026',isAI:false},
{league:'AFCON 2027 Qualifier',key:'afcon',match:'Senegal vs DR Congo',pred:'Senegal Win',analysis:'The Lions of Teranga are reigning AFCON champions and unbeaten in 9 home qualifiers. DR Congo are inconsistent away from home. Sadio Mané\'s leadership and the Dakar atmosphere give Senegal a clear edge.',odds:'1.70',via:'1xBet',conf:76,time:'19:00 UTC',date:'10 Jun 2026',isAI:false},
{league:'SA vs India · 1st Test',key:'cricket',match:'South Africa vs India',pred:'South Africa Win',analysis:'The Proteas have their strongest Test team in a decade. Rabada, Nortje and Jansen form the most feared pace attack in the world. India\'s batting is deep but they\'ve historically struggled against sustained world-class pace.',odds:'2.20',via:'Hollywoodbets',conf:60,time:'09:00 UTC',date:'10 Jun 2026',isAI:false},
// ── Football · 11 Jun 2026 · World Cup — BBC Sport confirmed ──
{league:'FIFA World Cup 2026 · Group A',key:'world',match:'Mexico vs South Africa',pred:'Mexico Win or Draw',analysis:'Bafana Bafana face a daunting World Cup opener against the hosts in front of a huge crowd. Mexico\'s attacking depth and passionate home support make them clear favourites. South Africa will defend deep — back Mexico to win or draw.',odds:'1.40',via:'Bet9ja',conf:72,time:'20:00 UTC',date:'11 Jun 2026',isAI:false},
// ── Boxing ──
{league:'WBC Heavyweight Championship',key:'boxing',match:'Oleksandr Usyk vs Daniel Dubois 2',pred:'Usyk Win',analysis:'Usyk is the most complete heavyweight of his generation — elite footwork, ring IQ and a chin tested at the highest level. In their first meeting Usyk\'s movement and jab neutralised Dubois\'s power entirely. Expect another masterclass.',odds:'1.45',via:'Bet9ja',conf:80,time:'21:00 UTC',date:'13 Jun 2026',isAI:false}
];

// ── NEWS ──────────────────────────────────────────────────────────────────────
const NEWS=[
{cat:'World Cup 2026',color:'#E60000',title:'World Cup 2026 Kicks Off June 11 – Mexico vs South Africa Opens the Tournament',date:'8 Jun 2026'},
{cat:'Nigeria',color:'#00875A',title:'Super Eagles Face Portugal in Pre-World Cup Friendly – 10 June',date:'7 Jun 2026'},
{cat:'CAF',color:'#C62828',title:'CAF Champions League Final Preview – Sundowns vs Al Ahly, 9 June',date:'7 Jun 2026'},
{cat:'Morocco',color:'#009A44',title:'Morocco World Cup 2026 Draw – Atlas Lions Group Stage Fixtures Confirmed',date:'6 Jun 2026'},
{cat:'Kenya',color:'#007A4D',title:'Betika Reaches 10 Million Users – New World Cup Features Added',date:'5 Jun 2026'},
{cat:'Africa',color:'#FF6B00',title:'Mobile Money Betting Surges 45% as World Cup 2026 Approaches',date:'4 Jun 2026'}
];

// ── ODDS DATA (fallback when live APIs are unavailable) ───────────────────────
const ODDS_DATA=[
// ── FIFA World Cup 2026 · Group Stage ─────────────────────────────────────────
{league:'FIFA World Cup 2026 · Group H',key:'world',live:false,home:'Spain',away:'Cape Verde',hScore:null,aScore:null,time:'15 Jun · 16:00 UTC',h:1.22,d:5.00,a:12.00,hBk:'Bet9ja',dBk:'1xBet',aBk:'SportyBet',complete:false},
{league:'FIFA World Cup 2026 · Group G',key:'world',live:false,home:'Belgium',away:'Egypt',hScore:null,aScore:null,time:'15 Jun · 19:00 UTC',h:1.57,d:3.60,a:5.50,hBk:'1xBet',dBk:'22Bet',aBk:'Bet9ja',complete:false},
{league:'FIFA World Cup 2026 · Group H',key:'world',live:false,home:'Saudi Arabia',away:'Uruguay',hScore:null,aScore:null,time:'15 Jun · 22:00 UTC',h:3.50,d:3.10,a:2.10,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'FIFA World Cup 2026 · Group G',key:'world',live:false,home:'Iran',away:'New Zealand',hScore:null,aScore:null,time:'16 Jun · 01:00 UTC',h:2.20,d:3.20,a:3.20,hBk:'1xBet',dBk:'Bet9ja',aBk:'Betway',complete:false},
{league:'FIFA World Cup 2026 · Group I',key:'world',live:false,home:'France',away:'Senegal',hScore:null,aScore:null,time:'16 Jun · 19:00 UTC',h:1.45,d:3.90,a:7.00,hBk:'Bet9ja',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'FIFA World Cup 2026 · Group J',key:'world',live:false,home:'Argentina',away:'Algeria',hScore:null,aScore:null,time:'17 Jun · 01:00 UTC',h:1.35,d:4.00,a:9.00,hBk:'SportyBet',dBk:'Betway',aBk:'1xBet',complete:false},
{league:'FIFA World Cup 2026 · Group G',key:'world',live:false,home:'Austria',away:'Jordan',hScore:null,aScore:null,time:'17 Jun · 04:00 UTC',h:1.50,d:3.70,a:6.50,hBk:'Bet9ja',dBk:'1xBet',aBk:'Melbet',complete:false},
{league:'FIFA World Cup 2026 · Group D',key:'world',live:false,home:'England',away:'Croatia',hScore:null,aScore:null,time:'17 Jun · 20:00 UTC',h:1.75,d:3.40,a:4.80,hBk:'1xBet',dBk:'Bet9ja',aBk:'22Bet',complete:false},
{league:'FIFA World Cup 2026 · Group J',key:'world',live:false,home:'Uzbekistan',away:'Colombia',hScore:null,aScore:null,time:'18 Jun · 02:00 UTC',h:4.00,d:3.30,a:1.85,hBk:'Betway',dBk:'22Bet',aBk:'1xBet',complete:false},
{league:'FIFA World Cup 2026 · Group B',key:'world',live:false,home:'Canada',away:'Qatar',hScore:null,aScore:null,time:'18 Jun · 22:00 UTC',h:1.80,d:3.40,a:4.50,hBk:'Bet9ja',dBk:'1xBet',aBk:'Betway',complete:false},
// ── AFCON 2027 Qualifiers · Round 3 ──────────────────────────────────────────
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Nigeria',away:'Rwanda',hScore:null,aScore:null,time:'16 Jun · 16:00 UTC',h:1.65,d:3.90,a:5.50,hBk:'Bet9ja',dBk:'SportPesa',aBk:'1xBet',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Senegal',away:'Ghana',hScore:null,aScore:null,time:'16 Jun · 19:00 UTC',h:2.10,d:3.10,a:3.20,hBk:'1xBet',dBk:'22Bet',aBk:'Betway',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Cameroon',away:'Algeria',hScore:null,aScore:null,time:'17 Jun · 18:00 UTC',h:2.30,d:3.10,a:3.00,hBk:'22Bet',dBk:'Bet9ja',aBk:'1xBet',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Morocco',away:'Zambia',hScore:null,aScore:null,time:'17 Jun · 19:00 UTC',h:1.50,d:3.80,a:6.50,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Egypt',away:'Zimbabwe',hScore:null,aScore:null,time:'17 Jun · 16:00 UTC',h:1.55,d:3.60,a:6.00,hBk:'22Bet',dBk:'Betway',aBk:'Bet9ja',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'South Africa',away:'Namibia',hScore:null,aScore:null,time:'18 Jun · 17:00 UTC',h:1.70,d:3.50,a:5.00,hBk:'Hollywoodbets',dBk:'Betway',aBk:'1xBet',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'DR Congo',away:'Kenya',hScore:null,aScore:null,time:'18 Jun · 15:00 UTC',h:1.80,d:3.30,a:4.50,hBk:'Bet9ja',dBk:'1xBet',aBk:'Betway',complete:false},
{league:'AFCON 2027 Qualifier · Round 3',key:'afcon',live:false,home:'Ivory Coast',away:'Ethiopia',hScore:null,aScore:null,time:'18 Jun · 16:00 UTC',h:1.55,d:3.70,a:5.50,hBk:'1xBet',dBk:'22Bet',aBk:'Betway',complete:false},
// ── CAF Confederation Cup ─────────────────────────────────────────────────────
{league:'CAF Confederation Cup · Final',key:'cafl',live:false,home:'Zamalek',away:'Petro de Luanda',hScore:null,aScore:null,time:'14 Jun · 19:00 UTC',h:2.10,d:3.20,a:3.40,hBk:'Betway',dBk:'Bet9ja',aBk:'22Bet',complete:false},
{league:'CAF Champions League 2026-27 · Prelim',key:'cafl',live:false,home:'TP Mazembe',away:'USM Alger',hScore:null,aScore:null,time:'18 Jun · 17:00 UTC',h:1.95,d:3.20,a:3.80,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'CAF Champions League 2026-27 · Prelim',key:'cafl',live:false,home:'Al Ahly',away:'Wydad Casablanca',hScore:null,aScore:null,time:'19 Jun · 18:00 UTC',h:2.00,d:3.20,a:3.60,hBk:'Bet9ja',dBk:'Betway',aBk:'1xBet',complete:false},
// ── Local Football · Nigeria (NPFL) ──────────────────────────────────────────
{league:'Nigeria Premier Football League',key:'local',live:false,home:'Enyimba',away:'Rangers International',hScore:null,aScore:null,time:'14 Jun · 15:00 UTC',h:2.10,d:3.10,a:3.40,hBk:'Bet9ja',dBk:'SportyBet',aBk:'Betking',complete:false},
{league:'Nigeria Premier Football League',key:'local',live:false,home:'Remo Stars',away:'Kano Pillars',hScore:null,aScore:null,time:'15 Jun · 15:00 UTC',h:2.30,d:3.00,a:3.20,hBk:'Bet9ja',dBk:'SportyBet',aBk:'1xBet',complete:false},
{league:'Nigeria Premier Football League',key:'local',live:false,home:'Shooting Stars',away:'Sunshine Stars',hScore:null,aScore:null,time:'15 Jun · 16:00 UTC',h:2.20,d:3.10,a:3.30,hBk:'SportyBet',dBk:'Bet9ja',aBk:'Betking',complete:false},
// ── Local Football · Kenya (KPL) ──────────────────────────────────────────────
{league:'Kenya Premier League',key:'local',live:false,home:'Gor Mahia',away:'AFC Leopards',hScore:null,aScore:null,time:'14 Jun · 14:00 UTC',h:2.00,d:3.10,a:3.60,hBk:'SportPesa',dBk:'Betika',aBk:'Odibets',complete:false},
{league:'Kenya Premier League',key:'local',live:false,home:'Kakamega Homeboyz',away:'Bandari',hScore:null,aScore:null,time:'15 Jun · 14:00 UTC',h:2.40,d:3.10,a:2.90,hBk:'Betika',dBk:'SportPesa',aBk:'1xBet',complete:false},
{league:'Kenya Premier League',key:'local',live:false,home:'Kenya Police FC',away:'Tusker FC',hScore:null,aScore:null,time:'16 Jun · 13:00 UTC',h:2.50,d:3.10,a:2.80,hBk:'SportPesa',dBk:'Betika',aBk:'1xBet',complete:false},
// ── Local Football · Ghana (GPL) ──────────────────────────────────────────────
{league:'Ghana Premier League',key:'local',live:false,home:'Asante Kotoko',away:'Hearts of Oak',hScore:null,aScore:null,time:'15 Jun · 16:00 UTC',h:2.10,d:3.10,a:3.40,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'Ghana Premier League',key:'local',live:false,home:'Medeama',away:'Legon Cities',hScore:null,aScore:null,time:'16 Jun · 16:00 UTC',h:2.30,d:3.00,a:3.20,hBk:'1xBet',dBk:'Betway',aBk:'22Bet',complete:false},
{league:'Ghana Premier League',key:'local',live:false,home:'Dreams FC',away:'Bechem United',hScore:null,aScore:null,time:'17 Jun · 15:00 UTC',h:2.20,d:3.10,a:3.30,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
// ── Local Football · South Africa (PSL) ──────────────────────────────────────
{league:'Betway Premiership',key:'local',live:false,home:'Mamelodi Sundowns',away:'Orlando Pirates',hScore:null,aScore:null,time:'14 Jun · 17:00 UTC',h:1.80,d:3.30,a:4.00,hBk:'Betway',dBk:'Hollywoodbets',aBk:'1xBet',complete:false},
{league:'Betway Premiership',key:'local',live:false,home:'Kaizer Chiefs',away:'Cape Town City',hScore:null,aScore:null,time:'15 Jun · 17:00 UTC',h:2.10,d:3.20,a:3.40,hBk:'Hollywoodbets',dBk:'Betway',aBk:'1xBet',complete:false},
{league:'Betway Premiership',key:'local',live:false,home:'Stellenbosch FC',away:'AmaZulu',hScore:null,aScore:null,time:'17 Jun · 17:00 UTC',h:2.30,d:3.10,a:3.00,hBk:'Betway',dBk:'Hollywoodbets',aBk:'1xBet',complete:false},
// ── Local Football · Egypt (EPL) ──────────────────────────────────────────────
{league:'Egyptian Premier League',key:'local',live:false,home:'Al Ahly',away:'Zamalek',hScore:null,aScore:null,time:'16 Jun · 17:00 UTC',h:1.90,d:3.30,a:3.90,hBk:'22Bet',dBk:'Betway',aBk:'1xBet',complete:false},
{league:'Egyptian Premier League',key:'local',live:false,home:'Pyramids FC',away:'Smouha',hScore:null,aScore:null,time:'17 Jun · 16:00 UTC',h:1.80,d:3.30,a:4.20,hBk:'1xBet',dBk:'22Bet',aBk:'Betway',complete:false},
// ── Local Football · Morocco (Botola Pro) ────────────────────────────────────
{league:'Botola Pro',key:'local',live:false,home:'Wydad Casablanca',away:'Raja Casablanca',hScore:null,aScore:null,time:'15 Jun · 18:00 UTC',h:2.00,d:3.20,a:3.70,hBk:'Betway',dBk:'1xBet',aBk:'22Bet',complete:false},
{league:'Botola Pro',key:'local',live:false,home:'FAR Rabat',away:'Moghreb Tetouan',hScore:null,aScore:null,time:'16 Jun · 18:00 UTC',h:2.10,d:3.10,a:3.40,hBk:'1xBet',dBk:'Betway',aBk:'22Bet',complete:false},
// ── Local Football · Tanzania ─────────────────────────────────────────────────
{league:'NBC Premier League',key:'local',live:false,home:'Simba SC',away:'Young Africans',hScore:null,aScore:null,time:'14 Jun · 13:00 UTC',h:2.20,d:3.10,a:3.20,hBk:'Betway',dBk:'SportPesa',aBk:'1xBet',complete:false},
// ── Local Football · Uganda ───────────────────────────────────────────────────
{league:'FUFA Premier League',key:'local',live:false,home:'KCCA FC',away:'Express FC',hScore:null,aScore:null,time:'15 Jun · 13:00 UTC',h:2.10,d:3.10,a:3.50,hBk:'Betway',dBk:'SportPesa',aBk:'1xBet',complete:false},
// ── Basketball · NBA Finals 2026 ──────────────────────────────────────────────
{league:'NBA Finals 2026 · Game 4',key:'basketball',live:false,home:'Oklahoma City Thunder',away:'New York Knicks',hScore:null,aScore:null,time:'14 Jun · 01:00 UTC',h:2.10,d:0,a:1.75,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
{league:'NBA Finals 2026 · Game 5',key:'basketball',live:false,home:'New York Knicks',away:'Oklahoma City Thunder',hScore:null,aScore:null,time:'17 Jun · 01:00 UTC',h:1.90,d:0,a:2.00,hBk:'1xBet',dBk:'',aBk:'Betway',complete:false},
{league:'NBA Finals 2026 · Game 6',key:'basketball',live:false,home:'Oklahoma City Thunder',away:'New York Knicks',hScore:null,aScore:null,time:'20 Jun · 01:00 UTC',h:2.00,d:0,a:1.90,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
// ── Tennis · ATP Queen's Club Championship ───────────────────────────────────
{league:"ATP · Queen's Club Championship",key:'tennis',live:false,home:'Carlos Alcaraz',away:'Tommy Paul',hScore:null,aScore:null,time:'13 Jun · 13:00 UTC',h:1.55,d:0,a:2.50,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
{league:"ATP · Queen's Club Championship",key:'tennis',live:false,home:'Novak Djokovic',away:'Alex de Minaur',hScore:null,aScore:null,time:'14 Jun · 14:00 UTC',h:1.70,d:0,a:2.20,hBk:'1xBet',dBk:'',aBk:'22Bet',complete:false},
{league:"ATP · Queen's Club Championship · Final",key:'tennis',live:false,home:'Carlos Alcaraz',away:'Jannik Sinner',hScore:null,aScore:null,time:'15 Jun · 14:00 UTC',h:1.80,d:0,a:2.05,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
// ── Tennis · WTA Eastbourne International ────────────────────────────────────
{league:'WTA · Eastbourne International',key:'tennis',live:false,home:'Iga Swiatek',away:'Elena Rybakina',hScore:null,aScore:null,time:'14 Jun · 12:00 UTC',h:1.65,d:0,a:2.30,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
{league:'WTA · Eastbourne International',key:'tennis',live:false,home:'Coco Gauff',away:'Barbora Krejcikova',hScore:null,aScore:null,time:'15 Jun · 11:00 UTC',h:1.70,d:0,a:2.20,hBk:'1xBet',dBk:'',aBk:'Betway',complete:false},
{league:'WTA · Eastbourne International · Final',key:'tennis',live:false,home:'Iga Swiatek',away:'Coco Gauff',hScore:null,aScore:null,time:'16 Jun · 13:00 UTC',h:1.55,d:0,a:2.50,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
// ── Cricket · Test Series ────────────────────────────────────────────────────
{league:'England vs India · 2nd Test',key:'cricket',live:false,home:'England',away:'India',hScore:null,aScore:null,time:'14 Jun · 10:00 UTC',h:2.30,d:3.00,a:2.10,hBk:'Hollywoodbets',dBk:'Betway',aBk:'1xBet',complete:false},
{league:'South Africa vs Pakistan · 1st T20',key:'cricket',live:false,home:'South Africa',away:'Pakistan',hScore:null,aScore:null,time:'15 Jun · 17:00 UTC',h:1.85,d:0,a:2.00,hBk:'Hollywoodbets',dBk:'',aBk:'Betway',complete:false},
{league:'South Africa vs Pakistan · 2nd T20',key:'cricket',live:false,home:'South Africa',away:'Pakistan',hScore:null,aScore:null,time:'18 Jun · 17:00 UTC',h:1.80,d:0,a:2.05,hBk:'Hollywoodbets',dBk:'',aBk:'Betway',complete:false},
{league:'Zimbabwe vs Ireland · ODI',key:'cricket',live:false,home:'Zimbabwe',away:'Ireland',hScore:null,aScore:null,time:'17 Jun · 08:00 UTC',h:2.40,d:0,a:1.65,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
// ── Rugby · NRL Round 15 ─────────────────────────────────────────────────────
{league:'NRL · Round 15',key:'rugby',live:false,home:'Melbourne Storm',away:'Penrith Panthers',hScore:null,aScore:null,time:'14 Jun · 09:00 UTC',h:2.20,d:0,a:1.75,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
{league:'NRL · Round 15',key:'rugby',live:false,home:'Sydney Roosters',away:'Parramatta Eels',hScore:null,aScore:null,time:'14 Jun · 11:00 UTC',h:2.00,d:0,a:1.90,hBk:'1xBet',dBk:'',aBk:'Betway',complete:false},
{league:'NRL · Round 15',key:'rugby',live:false,home:'Brisbane Broncos',away:'South Sydney Rabbitohs',hScore:null,aScore:null,time:'13 Jun · 09:30 UTC',h:1.90,d:0,a:2.00,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
{league:'NRL · Round 15',key:'rugby',live:false,home:'Canterbury Bulldogs',away:'Manly Sea Eagles',hScore:null,aScore:null,time:'15 Jun · 09:30 UTC',h:2.10,d:0,a:1.80,hBk:'1xBet',dBk:'',aBk:'Betway',complete:false},
// ── International Rugby Tests ────────────────────────────────────────────────
{league:'Rugby June Internationals',key:'rugby',live:false,home:'South Africa',away:'Scotland',hScore:null,aScore:null,time:'13 Jun · 15:00 UTC',h:1.45,d:0,a:2.80,hBk:'Hollywoodbets',dBk:'',aBk:'Betway',complete:false},
{league:'Rugby June Internationals',key:'rugby',live:false,home:'New Zealand',away:'Italy',hScore:null,aScore:null,time:'14 Jun · 10:00 UTC',h:1.25,d:0,a:4.50,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
// ── Baseball · MLB Regular Season ────────────────────────────────────────────
{league:'MLB · Regular Season',key:'baseball',live:false,home:'New York Yankees',away:'Boston Red Sox',hScore:null,aScore:null,time:'13 Jun · 23:05 UTC',h:1.90,d:0,a:2.00,hBk:'1xBet',dBk:'',aBk:'22Bet',complete:false},
{league:'MLB · Regular Season',key:'baseball',live:false,home:'Los Angeles Dodgers',away:'San Francisco Giants',hScore:null,aScore:null,time:'14 Jun · 02:10 UTC',h:1.75,d:0,a:2.15,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
{league:'MLB · Regular Season',key:'baseball',live:false,home:'Chicago Cubs',away:'St Louis Cardinals',hScore:null,aScore:null,time:'14 Jun · 23:20 UTC',h:1.95,d:0,a:1.95,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
{league:'MLB · Regular Season',key:'baseball',live:false,home:'Houston Astros',away:'Texas Rangers',hScore:null,aScore:null,time:'15 Jun · 00:10 UTC',h:1.95,d:0,a:1.95,hBk:'1xBet',dBk:'',aBk:'22Bet',complete:false},
{league:'MLB · Regular Season',key:'baseball',live:false,home:'Atlanta Braves',away:'New York Mets',hScore:null,aScore:null,time:'15 Jun · 22:20 UTC',h:1.85,d:0,a:2.05,hBk:'Betway',dBk:'',aBk:'1xBet',complete:false},
// ── Boxing ───────────────────────────────────────────────────────────────────
{league:'WBC Heavyweight Championship',key:'boxing',live:false,home:'Oleksandr Usyk',away:'Daniel Dubois',hScore:null,aScore:null,time:'13 Jun · 21:00 UTC',h:1.45,d:0,a:2.75,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false},
{league:'WBO Super Middleweight',key:'boxing',live:false,home:'Canelo Alvarez',away:'David Benavidez',hScore:null,aScore:null,time:'21 Jun · 02:00 UTC',h:1.75,d:0,a:2.10,hBk:'Bet9ja',dBk:'',aBk:'1xBet',complete:false}
];

// ── PAGE CONTENT (modals) ─────────────────────────────────────────────────────
const PAGE_CONTENT={
about:`<h1>About SifuFinds</h1>
<p>SifuFinds is Africa's leading independent betting comparison platform, providing verified bonus information, live odds, free tips, and country-specific bookmaker reviews across 23 African countries.</p>
<h2>Our Mission</h2>
<p>We help African bettors find the best bonuses, safest licensed operators, and most relevant local payment methods — all in their local currency.</p>
<div class="info-box">All bonuses are independently verified by our editorial team. Odds data refreshes every 15 seconds. Country data is updated daily.</div>
<h2>What We Cover</h2>
<div class="cg"><div class="cc"><h3>🏆 Best Bonuses</h3><p>Verified welcome bonuses, no-deposit offers, and free bets from licensed bookmakers.</p></div><div class="cc"><h3>💡 Free Tips</h3><p>Daily expert predictions and AI-powered tips for African and international football.</p></div><div class="cc"><h3>📊 Live Odds</h3><p>Real-time odds comparison across CAF CL, AFCON, EPL, and local leagues.</p></div><div class="cc"><h3>🌍 Countries</h3><p>23 African countries covered with local currency, payment methods, and licensed operators.</p></div></div>
<h2>18+ Only</h2><p>SifuFinds is strictly for adults aged 18 and over. Gambling involves financial risk. Please gamble responsibly.</p>`,
responsible:`<h1>Responsible Gambling</h1>
<div class="danger-box">⚠️ Gambling involves risk. Never bet more than you can afford to lose. If gambling is affecting your life, seek help immediately.</div>
<h2>Getting Help</h2>
<div class="hotline">📞 GamCare: 0808 8020 133 (UK) | BeGambleAware: begambleaware.org | NCPG Africa: ncpgafrica.org</div>
<h2>Signs of Problem Gambling</h2>
<ul><li>Betting with money needed for essentials (rent, food, bills)</li><li>Chasing losses by placing bigger bets</li><li>Hiding gambling activity from family or friends</li><li>Feeling anxious, irritable, or depressed when not gambling</li><li>Borrowing money to gamble</li></ul>
<h2>Self-Help Tools</h2>
<p>Most licensed African bookmakers offer deposit limits, session time limits, self-exclusion, and cooling-off periods. Contact your bookmaker's responsible gambling team to activate these tools.</p>
<div class="info-box">You can self-exclude from multiple bookmakers at once via your country's gambling regulator (NLRC in Nigeria, BCLB in Kenya, GCA in Ghana, WCGRB in South Africa).</div>
<h2>Safe Gambling Tips</h2>
<ul><li>Set a strict weekly budget before you start</li><li>Never chase your losses</li><li>Treat betting as entertainment, not income</li><li>Take regular breaks</li><li>Never bet under the influence of alcohol</li></ul>`,
privacy:`<h1>Privacy Policy</h1>
<p>Last updated: ${DATE_STR}</p>
<h2>Information We Collect</h2>
<p>SifuFinds does not collect personal data beyond standard web analytics (anonymous page views, country of origin). We use cookies to remember your country preference and improve your experience.</p>
<h2>Cookies</h2>
<p>We use a single cookie (<code>ab_country</code>) to save your selected country. No tracking cookies from ad networks are placed without consent.</p>
<h2>Third-Party Links</h2>
<p>SifuFinds contains affiliate links to licensed bookmakers. When you click a link we may receive a commission at no extra cost to you. We are not responsible for the privacy practices of third-party sites.</p>
<h2>Contact</h2><p>For privacy enquiries: privacy@sifufinds.com</p>`,
terms:`<h1>Terms of Use</h1>
<p>Last updated: ${DATE_STR}</p>
<h2>Disclaimer</h2>
<p>SifuFinds is an independent affiliate comparison website. Bonus information is provided for informational purposes only. Always verify current offers directly with the bookmaker before depositing.</p>
<h2>18+ Only</h2>
<p>This site is strictly for persons aged 18 or over. By using this site you confirm you are of legal gambling age in your jurisdiction.</p>
<h2>Affiliate Disclosure</h2>
<p>Some links on SifuFinds are affiliate links. We may receive compensation when you sign up with a bookmaker through our links. This never affects our editorial independence or bonus ratings.</p>
<h2>Accuracy</h2>
<p>We strive to keep bonus information current but cannot guarantee accuracy at all times. Bookmakers may change offers without notice. Always check the operator's official site for the most up-to-date terms.</p>`,
contact:`<h1>Contact Us</h1>
<p>Have a question, correction, or advertiser enquiry? Get in touch.</p>
<div class="cg">
<div class="cc"><h3>📧 Editorial</h3><p>editorial@sifufinds.com<br>Bonus corrections, new operators</p></div>
<div class="cc"><h3>💼 Advertising</h3><p>advertise@sifufinds.com<br>Sponsored listings, banner ads</p></div>
<div class="cc"><h3>⚖️ Legal & Privacy</h3><p>legal@sifufinds.com<br>GDPR, data requests</p></div>
<div class="cc"><h3>🔒 Responsible Gambling</h3><p>help@sifufinds.com<br>Self-exclusion support</p></div>
</div>
<div class="warn-box">We aim to respond within 2 business days. For urgent bonus corrections please include the bookmaker name and specific error in your subject line.</div>`,
advertise:`<h1>Advertise With Us</h1>
<p>SifuFinds reaches over 500,000 monthly visitors across 23 African markets. Our audience are active sports bettors looking for the best bonuses and bookmakers.</p>
<h2>Advertising Options</h2>
<div class="cg">
<div class="cc"><h3>Featured Listing</h3><p>Top placement on the bonuses page for your target country. Includes logo, bonus highlight, and CTA button.</p></div>
<div class="cc"><h3>Banner Ads</h3><p>Display advertising across all pages. 320×50, 728×90, and 300×250 formats available.</p></div>
<div class="cc"><h3>Sponsored Tips</h3><p>Branded tip cards on the tips page, targeting specific leagues and countries.</p></div>
<div class="cc"><h3>Country Spotlight</h3><p>Dedicated country feature on the Countries page with extended description and top placement.</p></div>
</div>
<div class="info-box">We only work with licensed and regulated bookmakers. All sponsored content is clearly labelled. Contact advertise@sifufinds.com for a media kit.</div>`
};

// ── HELPERS ───────────────────────────────────────────────────────────────────
const H=(id,v)=>{const e=document.getElementById(id);if(e)e.innerHTML=v;};
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
const pm=p=>{const c=(PM_C[p]||'#888|#fff').split('|');return`<span class="pmc" style="background:${c[0]};color:${c[1]}">${p}</span>`;};
const stars=n=>'★'.repeat(Math.min(n,5))+'☆'.repeat(Math.max(0,5-n));
const openURL=url=>window.open(url,'_blank','noopener noreferrer');
// Maps bookmaker abbreviations to their real brand domains.
// Required for affiliate redirect URLs (reffpa.com, bwredir.com, etc.) where domain
// extraction would otherwise return the affiliate tracking domain, not the brand.
const BRAND_DOMAINS={
  'FP':'fairpari.com',
  '1X':'1xbet.com','MB':'melbet.com','BN':'betwinner.com',
  'PP':'paripesa.com','HB':'helabet.com','TTC':'tictacbets.co.za',
  'B9':'bet9ja.com','SB':'sportybet.com','SB2':'sportybet.com',
  'BK':'betking.com','BW':'betway.com','22':'22bet.com',
  'MZ':'mozzartbet.com','NB':'nairabet.com','MS':'msport.com',
  'BPW':'betpawa.com','BT':'betika.com','SP':'sportpesa.com',
  'OD':'odibets.com','BG':'bangbet.com','BB':'bangbet.com',
  'HW':'hollywoodbets.net','SUP':'supabets.com','10B':'10bet.co.za',
  'EB':'easybet.co.za','WS':'wsb.co.za','SPB':'sportingbet.co.za',
  'SUN':'sunbet.co.za','BF':'betfred.co.za','BTB':'bettabets.co.za',
  'JSB':'jsbsport.co.za','PAB':'playabet.co.za','PLB':'playbet.co.za',
  'SCH':'soccershop.co.za','1BT':'firstbet.co.za','BX':'betxchange.co.za',
  'TBB':'thababet.co.za','SP+':'supabets.com','PB':'premierbet.com',
  'BTA':'betano.com','BLB':'bolabet.com',
  'PB':'premierbet.com','BNZ':'bonanzabet.co.zm','RB':'rasbet.bet'
};
// Local logo assets — served from /assets/logos/ on the site root.
// These take priority over any remote service. Add new entries as logos are downloaded.
const LOCAL_LOGOS={
  'FP':'/assets/logos/fairpari.png?v=2',
  '1X':'/assets/logos/1xbet.png?v=2','MB':'/assets/logos/melbet.png',
  'BN':'/assets/logos/betwinner.png?v=2','PP':'/assets/logos/paripesa.png',
  'HB':'/assets/logos/helabet.png','TTC':'/assets/logos/tictacbets.png?v=2',
  'B9':'/assets/logos/bet9ja.png','SB':'/assets/logos/sportybet.png',
  'BK':'/assets/logos/betking.png','BW':'/assets/logos/betway.png',
  '22':'/assets/logos/22bet.png','MZ':'/assets/logos/mozzartbet.png',
  'BPW':'/assets/logos/betpawa.png','BT':'/assets/logos/betika.png',
  'SP':'/assets/logos/sportpesa.png','OD':'/assets/logos/odibets.png',
  'BG':'/assets/logos/bangbet.png','BB':'/assets/logos/bangbet.png',
  'HW':'/assets/logos/hollywoodbets.png?v=2','BTA':'/assets/logos/betano.png',
  'RB':'/assets/logos/rasbet.png',
};
const LOGO_DEV_TOKEN='pk_LOpmKYtCS3q3rhYX_rDd9A';
const logoDomain=(url,abbr='')=>{try{const brand=abbr&&BRAND_DOMAINS[abbr];return brand||new URL(url).hostname.replace(/^www\./,'');}catch(e){return '';}};
// logoUrl: local asset first, then logo.dev, then Google favicon as last resort.
const logoUrl=(url,abbr='')=>{
  if(abbr&&LOCAL_LOGOS[abbr])return LOCAL_LOGOS[abbr];
  const d=logoDomain(url,abbr);
  if(!d)return'';
  if(LOGO_DEV_TOKEN)return`https://img.logo.dev/${d}?token=${LOGO_DEV_TOKEN}&size=256&format=png`;
  return`https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://${d}&size=256`;
};
const logoFb=(url,abbr='')=>{const d=logoDomain(url,abbr);return d?`https://logo.clearbit.com/${d}?size=256`:'';}
// Reveal logo image immediately on load — no size threshold, no text fallback at all.
// On error: try Clearbit once, then leave container blank (clean empty square).
function _logoLoaded(img){img.style.opacity='1';}
function _imgFallback(img){
  if(!img._fb){img._fb=1;const s=img.getAttribute('data-fb');if(s){img.src=s;return;}}
  img.style.opacity='0';
}
// logoImg: renders ONLY the logo image. No text, no background treatment.
// Container bg is set by the caller — white for list cards, brand-color for featured/header.
const logoImg=(url,name,abbr,tc,w,r,hasBg)=>{
  const lsrc=logoUrl(url,abbr);
  if(!lsrc)return'';
  const lfb=logoFb(url,abbr);
  return`<img src="${lsrc}" data-fb="${lfb}" alt="${name} logo" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;padding:0;opacity:0;transition:opacity .2s" loading="eager" onload="_logoLoaded(this)" onerror="_imgFallback(this)">`;};;

// ── COUNTRY MANAGEMENT ────────────────────────────────────────────────────────
const _SUPPORTED_CTYS=new Set(['NG','KE','GH','ZA','TZ','UG','ZM','ET','CI','CM','SN','RW','ZW','MW','MZ','AO','CD','BW','NA','EG','MA','SL','LR']);
const _CTY_LS='sf_cty';
const _CTY_TS_LS='sf_cty_ts';
const _CTY_MANUAL_LS='sf_cty_manual';
// A VPN'd visitor's apparent country can change between visits. An auto-detected
// (non-manual) country is only trusted for this long before we re-check the IP,
// so switching VPN location and coming back gets reflected instead of staying
// pinned to whatever was first detected. A manual pick (dropdown, or a shared
// ?cty= link — see changeCountry/syncCountryUI) never expires.
const _CTY_TTL_MS=30*60*1000;
function _ctyStale(){
  const ts=+localStorage.getItem(_CTY_TS_LS)||0;
  return (Date.now()-ts)>_CTY_TTL_MS;
}

// Fire geo-IP request immediately so it resolves in parallel with page render.
// Skipped when an explicit ?cty= is present, the visitor manually picked a
// country, or the last auto-detection is still fresh. Capped at 2 s so init() never hangs.
const _geoFetch=(()=>{
  if(new URLSearchParams(location.search).get('cty'))return null;
  if(localStorage.getItem(_CTY_MANUAL_LS))return null;
  if(localStorage.getItem(_CTY_LS)&&!_ctyStale())return null;
  const req=fetch('https://ipapi.co/json/').then(r=>r.json()).catch(()=>null);
  const timeout=new Promise(res=>setTimeout(()=>res(null),2000));
  return Promise.race([req,timeout]);
})();

function getCurrentCountry(){
  return new URLSearchParams(window.location.search).get('cty')
    ||localStorage.getItem(_CTY_LS)
    ||'NG';
}
function changeCountry(code){
  localStorage.setItem(_CTY_LS,code);
  localStorage.setItem(_CTY_MANUAL_LS,'1');
  // Let the new country's default language (COUNTRY_LANG) take over unless the
  // visitor explicitly picks a language again afterward via the language switcher.
  localStorage.removeItem(_LANG_LS);
  // Reload the current page with no ?cty= param — the pick is carried entirely via
  // localStorage (see getCurrentCountry), so the URL bar never shows ?cty=XX. On
  // index.html this also lets the GEO HOMEPAGE ROUTING script send the visitor
  // straight to their real /best-betting-in-<slug>/ page on reload.
  const u=new URL(window.location.href);
  u.searchParams.delete('cty');
  window.location.href=u.toString();
}
function syncCountryUI(){
  const cty=getCurrentCountry();
  // If a URL param is present (e.g. an old shared ?cty= link), keep localStorage in
  // sync and treat it as an explicit choice, same as the dropdown, then strip it
  // from the visible URL immediately so ?cty= never lingers in the address bar.
  const urlCty=new URLSearchParams(window.location.search).get('cty');
  if(urlCty){
    localStorage.setItem(_CTY_LS,urlCty);
    localStorage.setItem(_CTY_MANUAL_LS,'1');
    const u=new URL(window.location.href);
    u.searchParams.delete('cty');
    history.replaceState(null,'',u.toString());
  }
  const sel=document.getElementById('ctySel');
  if(sel)sel.value=cty;
  document.querySelectorAll('.cty-q').forEach(b=>{
    const m=b.getAttribute('onclick')||'';
    b.classList.toggle('on',m.includes(`'${cty}'`));
  });
}

// Awaited by each page's init() before rendering.
// Resolves the visitor's country from geo-IP on first visit (or once the TTL
// above expires) and saves it. Always writes something to localStorage so a
// stale/failed lookup doesn't repeat on every page view.
async function waitForCountry(){
  if(!_geoFetch)return;
  try{
    const data=await _geoFetch;
    const code=data?.country_code?.toUpperCase();
    localStorage.setItem(_CTY_LS,code&&_SUPPORTED_CTYS.has(code)?code:'NG');
  }catch(e){
    localStorage.setItem(_CTY_LS,'NG');
  }
  localStorage.setItem(_CTY_TS_LS,String(Date.now()));
}

// ── NAVIGATION ────────────────────────────────────────────────────────────────
function goHome(){window.location.href=(typeof SITE!=='undefined'?SITE.home:'/');}
function goFilter(f){
  const base=typeof SITE!=='undefined'?SITE.home:'/';
  window.location.href=base+(base.includes('?')?'&':'?')+'filter='+f;
}
function gotoTips(tf){
  const base=typeof SITE!=='undefined'?SITE.tips:'/tips/';
  window.location.href=base+(base.includes('?')?'&':'?')+'tf='+tf;
}
function gotoCasino(cf){
  const base=typeof SITE!=='undefined'?SITE.casino:'/casino/';
  window.location.href=base+(base.includes('?')?'&':'?')+'cf='+cf;
}
function gotoOdds(lg){
  const base=typeof SITE!=='undefined'?SITE.odds:'/odds/';
  window.location.href=base+(base.includes('?')?'&':'?')+'lg='+lg;
}
function showCty(code){
  const base=typeof SITE!=='undefined'?SITE.countries:'/countries/';
  window.location.href=base+(base.includes('?')?'&':'?')+'sel='+code;
}

// ── MODALS ────────────────────────────────────────────────────────────────────
function openPage(type){
  const content=PAGE_CONTENT[type];
  if(!content)return;
  document.getElementById('page-content').innerHTML=content;
  document.getElementById('page-modal').classList.add('open');
  document.body.style.overflow='hidden';
}
function closePage(){
  document.getElementById('page-modal').classList.remove('open');
  document.body.style.overflow='';
}
// close page modal on background click
document.addEventListener('click',e=>{
  if(e.target.id==='page-modal'){closePage();}
});

// ── ROTATING OFFER POPUP ─────────────────────────────────────────────────────
// Fires once per browser tab (sessionStorage-gated) after 30s on any landing page.
// Offers are shuffled from the visitor's country BOOKS list each time, so the 3
// brands shown keep changing between sessions and page visits.
const _OFFER_POPUP_SS='sf_offer_popup_shown';
const _OFFER_POPUP_DELAY_MS=30000;
function _pickRandomOffers(cty,n){
  const pool=(BOOKS[cty]||BOOKS.NG).slice();
  for(let i=pool.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));
    [pool[i],pool[j]]=[pool[j],pool[i]];
  }
  return pool.slice(0,n);
}
function _offerCard(b){
  return`<div class="fc">
    <div class="fc-img" style="background:${b.bg}">
      ${logoImg(b.url,b.name,b.abbr,b.tc,140,12,true)}
      <span class="fc-nm">${b.name}</span>
    </div>
    <div class="fc-body">
      <div class="fc-off">${b.off}</div>
      <a class="gbtn" href="${b.url}" target="_blank" rel="noopener noreferrer sponsored">Claim →</a>
    </div>
  </div>`;
}
function closeOfferPopup(){
  const bg=document.getElementById('offer-popup-bg');
  if(bg)bg.remove();
  document.body.style.overflow='';
}
function showOfferPopup(){
  if(sessionStorage.getItem(_OFFER_POPUP_SS))return;
  if(document.getElementById('cmp-modal')?.classList.contains('open'))return;
  if(document.getElementById('page-modal')?.classList.contains('open'))return;
  const cty=getCurrentCountry();
  const cd=(typeof COUNTRY_DATA!=='undefined'&&COUNTRY_DATA[cty])||null;
  const offers=_pickRandomOffers(cty,3);
  if(offers.length<3)return;
  sessionStorage.setItem(_OFFER_POPUP_SS,'1');
  const el=document.createElement('div');
  el.id='offer-popup-bg';
  el.className='offer-popup-bg open';
  el.innerHTML=`<div class="offer-popup">
    <button class="offer-popup-close" onclick="closeOfferPopup()">×</button>
    <h2>🔥 Top ${cd?cd.name:'Betting'} Offers Right Now</h2>
    <p class="op-sub">Verified bonuses from licensed bookmakers — updated live.</p>
    <div class="op-grid">${offers.map(_offerCard).join('')}</div>
    <p class="op-dis">18+ only. T&amp;Cs apply. Bet responsibly. <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer">BeGambleAware.org</a></p>
  </div>`;
  document.body.appendChild(el);
  document.body.style.overflow='hidden';
  el.addEventListener('click',e=>{if(e.target===el)closeOfferPopup();});
}
setTimeout(showOfferPopup,_OFFER_POPUP_DELAY_MS);

// ── EXPAND / COLLAPSE DETAILS ─────────────────────────────────────────────────
function toggleDet(btn){
  const det=btn.nextElementSibling;
  const isOpen=det.classList.contains('open');
  document.querySelectorAll('.xdet.open').forEach(d=>{
    d.classList.remove('open');
    if(d.previousElementSibling&&d.previousElementSibling.classList.contains('xbtn'))
      d.previousElementSibling.innerHTML='▼ More details';
  });
  if(!isOpen){
    det.classList.add('open');
    btn.innerHTML='▲ Hide details';
  }
}

// ── COMPARE ───────────────────────────────────────────────────────────────────
let _cmpList=[];
function toggleCmp(idx,name,bg,tc,abbr,url){
  const ex=_cmpList.findIndex(c=>c.idx===idx);
  if(ex>=0){_cmpList.splice(ex,1);}
  else if(_cmpList.length<4){_cmpList.push({idx,name,bg,tc,abbr,url:url||''});}
  _renderCmpBar();
}
function removeCmp(idx){_cmpList=_cmpList.filter(c=>c.idx!==idx);_renderCmpBar();}
function clearCompare(){_cmpList=[];_renderCmpBar();}
function _renderCmpBar(){
  const bar=document.getElementById('cmp-bar');
  if(!bar)return;
  if(_cmpList.length===0){bar.classList.remove('show');return;}
  bar.classList.add('show');
  document.getElementById('cmp-items').innerHTML=_cmpList.map(c=>
    `<div class="cmp-chip"><div style="width:18px;height:18px;border-radius:3px;background:${c.bg};overflow:hidden;flex-shrink:0;position:relative">${logoImg(c.url,c.name,c.abbr,c.tc,16,2,true)}</div>${c.name}<button onclick="removeCmp(${c.idx})">×</button></div>`
  ).join('');
}
function openCompare(){
  const cty=getCurrentCountry();
  const books=BOOKS[cty]||BOOKS.NG;
  const sel=_cmpList.map(c=>books[c.idx]).filter(Boolean);
  if(sel.length<2)return;
  const fields=[['Bonus Offer','off'],['Min Deposit','min'],['Cash Out','cashout'],['Live Stream','stream'],['Instant Pay','instant'],['No Deposit','nodep'],['Sports','sports'],['Licence','lic']];
  let html=`<table class="cmp-table"><thead><tr><th>Feature</th>${sel.map(b=>`<th><div class="cmp-logo-cell"><div class="cmp-mini-logo" style="background:${b.bg};overflow:hidden">${logoImg(b.url,b.name,b.abbr,b.tc,28,4,true)}</div>${b.name}</div></th>`).join('')}</tr></thead><tbody>`;
  fields.forEach(([label,key])=>{
    html+=`<tr><td><strong>${label}</strong></td>${sel.map(b=>{
      const v=b[key];
      if(typeof v==='boolean')return`<td class="${v?'yes':'no'}">${v?'✓ Yes':'✗ No'}</td>`;
      return`<td>${v}</td>`;
    }).join('')}</tr>`;
  });
  html+=`</tbody></table>`;
  document.getElementById('cmp-table-wrap').innerHTML=html;
  document.getElementById('cmp-modal').classList.add('open');
}
document.addEventListener('click',e=>{
  if(e.target.id==='cmp-modal')document.getElementById('cmp-modal').classList.remove('open');
});

// ── HEADER BRANDS BAR ─────────────────────────────────────────────────────────
// FairPari first (per 2026-08-10 direction — top affiliate placement in every
// country list + featured bar), then TicTacBets, BetXchange, Bettabets (per
// 2026-08-08 direction), then the rest in their prior relative order.
const HEADER_BRANDS=[
{name:'TicTacBets',abbr:'TTC',bg:'#CC0000',tc:'#fff',url:'https://trackrt.tictacbets.co.za/o/zdY0CA?site_id=1023',domain:'tictacbets.co.za',tag:'25 Free Spins + R5K'},
{name:'BetXchange',abbr:'BX',bg:'#0D47A1',tc:'#fff',url:'https://track.trkbxa.click/o/yDSAGh?lpage=m0gk2w&site_id=1226',domain:'betxchange.co.za',tag:'R200 Free Bet on First Deposit'},
{name:'Bettabets',abbr:'BTB',bg:'#1B5E20',tc:'#fff',url:'https://track.bettapartners.co.za/o/zNV2Pk?lpage=AjB-aC&site_id=777',domain:'bettabets.co.za',tag:'R200 Free Bet on First Deposit'},
{name:'FairPari',abbr:'FP',bg:'#1677FF',tc:'#fff',url:'https://fairpaff.top/L?tag=d_5941712m_72465c_&site=5941712&ad=72465&r=registration',domain:'fairpari.com',tag:'100% Bonus – Up to €100'},
{name:'1xBet',abbr:'1X',bg:'#276AA5',tc:'#fff',url:'https://reffpa.com/L?tag=d_3805082m_97c_&site=3805082&ad=97',domain:'1xbet.com',tag:'Up to ₦1.2M Bonus'},
{name:'BetWinner',abbr:'BN',bg:'#009277',tc:'#fff',url:'https://bwredir.com/1Lvf?p=%2Fregistration%2F',domain:'betwinner.com',tag:'200% Welcome Bonus'},
{name:'HelaBet',abbr:'HB',bg:'#430084',tc:'#fff',url:'https://1212fghnna.com/L?tag=d_2204817m_52235c_&site=2204817&ad=52235',domain:'helabet.com',tag:'100% Welcome Bonus'},
{name:'Melbet',abbr:'MB',bg:'#212121',tc:'#fff',url:'https://refpa3665.com/L?tag=d_3805306m_61559c_&site=3805306&ad=61559',domain:'melbet.com',tag:'200% + 150 Sports'},
{name:'Paripesa',abbr:'PP',bg:'#172BE2',tc:'#fff',url:'https://combodef.com/L?tag=d_2350859m_45569c_&site=2350859&ad=45569',domain:'paripesa.com',tag:'200% First Deposit'}
];
function renderBrandsBar(){
  const el=document.getElementById('hbrands');
  if(!el)return;
  el.innerHTML=`<div class="hbrands-in"><span class="hbrands-lbl">🔥 Featured</span><div class="hbrands-list">${
    HEADER_BRANDS.map(b=>{const logoSrc=b.domain?`https://${b.domain}`:b.url;return`<a class="hbrand" href="${b.url}" target="_blank" rel="noopener noreferrer sponsored" style="background:${b.bg};color:${b.tc}"><div class="hbrand-logo">${logoImg(logoSrc,b.name,b.abbr,b.tc,22,3,true)}</div><div class="hbrand-body"><span class="hbrand-name">${b.name}</span><span class="hbrand-tag">${b.tag}</span></div><span class="hbrand-cta">Bet Now →</span></a>`;}).join('')
  }</div></div>`;
}
document.addEventListener('DOMContentLoaded',renderBrandsBar);

// Relative path prefix from the current page back to the site root, e.g.
// '../../' from /countries/nigeria/, '../' from /tips/, '' from /.
function _pathRoot(){
  const segs=location.pathname.split('/').filter(Boolean);
  return '../'.repeat(segs.length);
}

// Inject About link into nav on every page (E-E-A-T trust signal)
document.addEventListener('DOMContentLoaded',function(){
  const tabs=document.querySelector('.ntabs');
  if(tabs&&!tabs.querySelector('[href*="about"]')){
    const root=_pathRoot();
    const a=document.createElement('a');
    a.className='nt';
    a.href=root+'about/';
    a.textContent='ℹ️ About';
    tabs.appendChild(a);
  }
});

// Mobile hamburger nav
document.addEventListener('DOMContentLoaded',function(){
  const mnavIn=document.querySelector('.mnav-in');
  if(!mnavIn)return;
  const btn=document.createElement('button');
  btn.className='mob-menu-btn';
  btn.setAttribute('aria-label','Toggle navigation menu');
  btn.innerHTML='&#9776;';
  mnavIn.appendChild(btn);
  btn.addEventListener('click',function(e){
    e.stopPropagation();
    const tabs=document.querySelector('.ntabs');
    if(!tabs)return;
    const open=tabs.classList.toggle('mob-open');
    btn.innerHTML=open?'&#x2715;':'&#9776;';
    btn.setAttribute('aria-expanded',open?'true':'false');
  });
  document.addEventListener('click',function(e){
    if(!e.target.closest('.mnav')){
      document.querySelector('.ntabs')?.classList.remove('mob-open');
      btn.innerHTML='&#9776;';
      btn.setAttribute('aria-expanded','false');
    }
  });
});

// ── SIFU ANALYTICS TRACKER ────────────────────────────────────────────────────
(function(){
  'use strict';
  var GA_ID='G-0B51MX2ZKE';
  var GC_SITE='sifufinds'; // sifufinds.goatcounter.com — live

  // ── Local event log (powers the /analytics.html dashboard) ──────────────────
  function logLocal(name,params){
    try{
      var ev=JSON.parse(localStorage.getItem('sf_events')||'[]');
      ev.unshift({t:Date.now(),n:name,p:params});
      localStorage.setItem('sf_events',JSON.stringify(ev.slice(0,500)));
    }catch(e){}
  }

  // ── GA4 (page views + events → Google Analytics) ────────────────────────────
  window.dataLayer=window.dataLayer||[];
  function gtag(){window.dataLayer.push(arguments);}
  // Only inject if not already present in <head> (avoids double-firing)
  if(!document.querySelector('script[src*="googletagmanager.com/gtag"]')){
    var gs=document.createElement('script');
    gs.async=true;gs.src='https://www.googletagmanager.com/gtag/js?id='+GA_ID;
    document.head.appendChild(gs);
    gtag('js',new Date());
    gtag('config',GA_ID,{send_page_view:true});
  }

  // ── GoatCounter (lightweight page views + custom events → goatcounter.com) ──
  if(!document.querySelector('script[data-goatcounter]')){
    var gcs=document.createElement('script');
    gcs.async=true;
    gcs.setAttribute('data-goatcounter','https://'+GC_SITE+'.goatcounter.com/count');
    gcs.src='https://gc.zgo.at/count.js';
    document.head.appendChild(gcs);
  }
  function gcEvent(path,title){
    // fires after GoatCounter has loaded
    if(window.goatcounter&&window.goatcounter.count){
      window.goatcounter.count({path:path,title:title,event:true});
    }
  }

  // ── Unified track helper ─────────────────────────────────────────────────────
  function track(name,params){
    logLocal(name,params);
    gtag('event',name,params||{});
  }
  window.sfTrack=track; // exposed so other modules (e.g. exit-intent engine) share one event pipe

  // Page impression (GA4 fires automatically; log locally too)
  logLocal('page_view',{page:location.pathname});

  // ── Outbound / affiliate clicks ──────────────────────────────────────────────
  document.addEventListener('click',function(e){
    var a=e.target.closest('a[href]');
    if(!a)return;
    var href=a.href||'';
    var ext=a.target==='_blank'||(href.indexOf('http')===0&&href.indexOf('sifufinds.com')===-1);
    if(!ext)return;
    var card=a.closest('.hbrand,.bk-card,.feat-card,.gs-item');
    var bkName=card?(card.querySelector('.hbrand-name,.bk-name,.feat-name,.gs-name')||{}).textContent:null;
    bkName=(bkName||a.textContent||'').trim().slice(0,60)||'unknown';
    var aff=typeof AFFILIATE_DOMAINS!=='undefined'&&AFFILIATE_DOMAINS.some(function(d){return href.indexOf(d)>-1;});
    track('outbound_click',{link:href.slice(0,200),bk:bkName,affiliate:aff,page:location.pathname});
    gcEvent('click/'+bkName.toLowerCase().replace(/\s+/g,'-'),bkName+' click');
  },true);

  // ── Scroll depth ─────────────────────────────────────────────────────────────
  var depths=[25,50,75,90],fired={};
  window.addEventListener('scroll',function(){
    var el=document.documentElement,body=document.body;
    var top=el.scrollTop||body.scrollTop;
    var h=Math.max(el.scrollHeight,body.scrollHeight)-el.clientHeight;
    if(!h)return;
    var pct=Math.min(100,Math.round(top/h*100));
    depths.forEach(function(d){
      if(pct>=d&&!fired[d]){fired[d]=1;track('scroll_depth',{pct:d,page:location.pathname});}
    });
  },{passive:true});

  // ── Engagement time ──────────────────────────────────────────────────────────
  var t0=Date.now(),engaged=0;
  document.addEventListener('visibilitychange',function(){
    if(document.hidden){engaged+=Date.now()-t0;}else{t0=Date.now();}
  });
  window.addEventListener('pagehide',function(){
    if(!document.hidden)engaged+=Date.now()-t0;
    if(engaged>3000)track('engagement',{secs:Math.round(engaged/1000),page:location.pathname});
  });

  // ── Filter clicks ────────────────────────────────────────────────────────────
  document.addEventListener('click',function(e){
    var b=e.target.closest('.fp,[data-f]');
    if(!b)return;
    track('filter',{v:(b.dataset.f||b.textContent||'').trim().slice(0,30)});
  });

  // ── Site search ──────────────────────────────────────────────────────────────
  var sTimer;
  document.addEventListener('input',function(e){
    if(e.target.id!=='srch-inp')return;
    clearTimeout(sTimer);
    sTimer=setTimeout(function(){
      var q=(e.target.value||'').trim();
      if(q.length>2)track('search',{q:q.slice(0,50)});
    },900);
  });
})();

// ── EXIT INTENT ENGINE ───────────────────────────────────────────────────────
// Behaviourally-triggered (not load-triggered) conversion surface — distinct
// from the 30s time-based showOfferPopup() above. Fires at most once per
// session, gated by genuine engagement, and shares showOfferPopup()'s own
// _OFFER_POPUP_SS session flag in both directions so a visitor is never shown
// two promotional interruptions in the same session (whichever fires first
// suppresses the other — see AGENT-KNOWLEDGE.md for the reasoning).
(function(){
  'use strict';

  const EXIT_INTENT_CONFIG={
    enabled:true,
    desktop:{enabled:true,minimumTime:15000,minimumScrollDepth:20},
    mobile:{enabled:true,minimumTime:15000,minimumScrollDepth:20},
    frequency:{sessionLimit:1,cooldownDays:7},
    // remaining (1-controlPct) traffic sees the page-appropriate experience below;
    // the control group's suppressed-but-logged sessions are what let GA4 measure
    // incremental lift instead of just popup-interaction rate.
    variants:{controlPct:0.15},
    experienceByCategory:{
      homepage:'commercial',country_home:'commercial',comparison:'commercial',
      review:'commercial',commercial_tool:'commercial',article:'content'
    },
    excludedCategories:['excluded'],
    analytics:{enabled:true}
  };
  if(!EXIT_INTENT_CONFIG.enabled)return;

  function lsGet(k){try{return localStorage.getItem(k);}catch(e){return null;}}
  function lsSet(k,v){try{localStorage.setItem(k,v);}catch(e){}}
  function ssGet(k){try{return sessionStorage.getItem(k);}catch(e){return null;}}
  function ssSet(k,v){try{sessionStorage.setItem(k,v);}catch(e){}}

  const LS_LAST_SHOWN='sf_ei_last_shown';
  const LS_BUCKET='sf_ei_bucket';
  const LS_FIRST_SEEN='sf_ei_first_seen';
  const SS_SESSION_LOGGED='sf_ei_session_logged';

  function pageCategory(){
    const p=location.pathname;
    if(/^\/(about|contact|privacy|press|analytics)(\/|\.html)?$/.test(p))return'excluded';
    if(p==='/'||p==='/index.html')return'homepage';
    if(/^\/best-betting-in-[^/]+\/?$/.test(p))return'country_home';
    if(/^\/best-bonus-in-[^/]+\/?$/.test(p))return'comparison';
    if(/^\/countries\/[^/]+\/[^/]+\/?$/.test(p))return'other';
    if(/^\/countries\/[^/]+\/?$/.test(p))return'country_home';
    if(/^\/blog\/[^/]+\/?$/.test(p))return'article';
    if(/^\/bookmakers\/[^/]+\/?$/.test(p))return'review';
    if(/^\/(tips|odds|leagues|casino)\/?$/.test(p))return'commercial_tool';
    if(/^\/(bonuses|guides|payments)\//.test(p))return'commercial_tool';
    return'other';
  }

  // Country -> URL slug. Kept in sync with index.html's geo-redirect MAP by hand
  // (see "Geo Homepage Routing" in CLAUDE.md) — add new countries to both.
  const CTY_SLUG={NG:'nigeria',KE:'kenya',GH:'ghana',ZA:'south-africa',TZ:'tanzania',UG:'uganda',ZM:'zambia',ET:'ethiopia',CI:'ivory-coast',CM:'cameroon',SN:'senegal',RW:'rwanda',ZW:'zimbabwe',MW:'malawi',MZ:'mozambique',AO:'angola',CD:'dr-congo',BW:'botswana',NA:'namibia',EG:'egypt',MA:'morocco',SL:'sierra-leone',LR:'liberia'};

  function trafficSource(){
    const ref=document.referrer;
    if(!ref)return'direct';
    try{
      const h=new URL(ref).hostname.replace(/^www\./,'');
      if(h.includes('sifufinds.com'))return'internal';
      if(/google\.|bing\.|duckduckgo\.|yahoo\./.test(h))return'search';
      if(/facebook\.|instagram\.|twitter\.|x\.com|t\.me|tiktok\./.test(h))return'social';
      return'referral';
    }catch(e){return'referral';}
  }

  function bucket(){
    let v=lsGet(LS_BUCKET);
    if(v==='control'||v==='treatment')return v;
    v=Math.random()<EXIT_INTENT_CONFIG.variants.controlPct?'control':'treatment';
    lsSet(LS_BUCKET,v);
    return v;
  }

  // First call ever (no LS_FIRST_SEEN yet) both answers "is this a returning
  // visitor?" (no) and plants the flag for next time — deliberately called
  // exactly once per trigger (cached in `returning` below) so the answer can't
  // flip mid-popup.
  function isReturningVisitor(){
    if(lsGet(LS_FIRST_SEEN))return true;
    lsSet(LS_FIRST_SEEN,String(Date.now()));
    return false;
  }

  const cat=pageCategory();
  if(EXIT_INTENT_CONFIG.excludedCategories.includes(cat))return;

  const device=('ontouchstart'in window||navigator.maxTouchPoints>0)?'mobile':'desktop';
  const cfg=device==='mobile'?EXIT_INTENT_CONFIG.mobile:EXIT_INTENT_CONFIG.desktop;
  if(!cfg.enabled)return;

  const last=parseInt(lsGet(LS_LAST_SHOWN)||'0',10);
  if(last&&Date.now()-last<EXIT_INTENT_CONFIG.frequency.cooldownDays*86400000)return;

  let converted=false,scrollPct=0,fired=false,eligibleLogged=false,lastModalCloseTs=0;
  const startTs=Date.now();

  // Reuses the click delegation the analytics tracker already installed above —
  // this is a second, independent listener, not a duplicate of that one.
  document.addEventListener('click',function(e){
    const a=e.target.closest('a[href]');
    if(!a)return;
    const href=a.href||'';
    if(typeof AFFILIATE_DOMAINS!=='undefined'&&AFFILIATE_DOMAINS.some(d=>href.includes(d)))converted=true;
  },true);

  window.addEventListener('scroll',function(){
    const el=document.documentElement,body=document.body;
    const top=el.scrollTop||body.scrollTop;
    const h=Math.max(el.scrollHeight,body.scrollHeight)-el.clientHeight;
    if(h>0)scrollPct=Math.max(scrollPct,Math.min(100,Math.round(top/h*100)));
  },{passive:true});

  function engaged(){
    return Date.now()-startTs>=cfg.minimumTime&&scrollPct>=cfg.minimumScrollDepth;
  }

  function midInteraction(){
    const ae=document.activeElement;
    if(ae&&/INPUT|TEXTAREA|SELECT/.test(ae.tagName))return true;
    if(document.getElementById('cmp-modal')?.classList.contains('open'))return true;
    if(document.getElementById('page-modal')?.classList.contains('open'))return true;
    if(document.getElementById('offer-popup-bg'))return true;
    if(Date.now()-lastModalCloseTs<5000)return true;
    return false;
  }

  function trackEvent(name,extra){
    if(!EXIT_INTENT_CONFIG.analytics.enabled||!window.sfTrack)return;
    window.sfTrack(name,Object.assign({page:location.pathname,category:cat,device,bucket:bucket(),source:trafficSource()},extra||{}));
  }

  function maybeTrigger(trigger){
    if(fired||converted||midInteraction())return;
    if(ssGet(_OFFER_POPUP_SS))return; // showOfferPopup() already interrupted this session
    if(!engaged())return;
    // Logged once per browser session (not once per qualifying page) so
    // control-bucket sessions — which never trip the suppression flag above —
    // can't rack up multiple exit_intent_session events across multi-page
    // browsing and skew the control-vs-treatment comparison this exists for.
    if(!eligibleLogged&&!ssGet(SS_SESSION_LOGGED)){
      eligibleLogged=true;
      ssSet(SS_SESSION_LOGGED,'1');
      trackEvent('exit_intent_session',{shown:bucket()==='treatment'});
    }
    if(bucket()!=='treatment')return; // control group: measured, never shown
    fired=true;
    open(trigger);
  }

  if(device==='desktop'){
    document.addEventListener('mouseleave',function(e){
      if(e.clientY>0||e.relatedTarget)return;
      maybeTrigger('mouseleave');
    });
  }else{
    // Fast upward scroll after real engagement — the closest natural analogue
    // to desktop exit intent on touch devices. Deliberately does NOT hook
    // popstate/back-button interception: that requires effectively hijacking
    // navigation (pushing a fake history entry to intercept "back"), which is
    // explicitly out of scope — it breaks the real back button for the visitor.
    let lastY=window.scrollY,lastT=Date.now(),ticking=false;
    window.addEventListener('scroll',function(){
      if(ticking)return;
      ticking=true;
      requestAnimationFrame(function(){
        const y=window.scrollY,t=Date.now(),dt=t-lastT;
        if(dt>0){
          const v=(lastY-y)/dt; // px/ms, positive = scrolling up
          if(v>0.9&&lastY-y>120)maybeTrigger('scroll_velocity');
        }
        lastY=y;lastT=t;ticking=false;
      });
    },{passive:true});
  }

  // Wrap (not replace) the existing close handlers so exit-intent inherits the
  // "don't ambush right after another modal closes" cooldown without touching
  // their own definitions above.
  ['closePage','closeOfferPopup'].forEach(fn=>{
    const orig=window[fn];
    if(typeof orig==='function'){
      window[fn]=function(){lastModalCloseTs=Date.now();return orig.apply(this,arguments);};
    }
  });

  const HEADLINES={
    homepage:n=>`Still deciding where to bet in ${n}?`,
    country_home:n=>`Still deciding where to bet in ${n}?`,
    comparison:n=>`Ready to claim the best bonus in ${n}?`,
    review:()=>'Before you decide, see today\'s top offer',
    commercial_tool:()=>'Don\'t miss today\'s top betting offer'
  };

  function buildExperience(){
    const cty=getCurrentCountry();
    const cd=(typeof COUNTRY_DATA!=='undefined'&&COUNTRY_DATA[cty])||null;
    const slug=CTY_SLUG[cty]||'nigeria';
    const cname=cd?cd.name:'Africa';

    if(cat==='article'){
      const links=Array.from(document.querySelectorAll('.related-posts a')).slice(0,2)
        .map(a=>({title:a.textContent.trim(),href:a.getAttribute('href')}));
      if(links.length){
        return{
          id:'content',goal:'engagement',
          headline:'Still exploring this topic?',
          bodyHtml:'<div class="ei-links">'+links.map(l=>`<a class="ei-link" href="${l.href}" data-ei-cta="content_link">${l.title} →</a>`).join('')+'</div>'
        };
      }
      // falls through to 'final' below if this post has no related-posts block
    }

    const expType=EXIT_INTENT_CONFIG.experienceByCategory[cat];
    if(expType==='commercial'&&typeof BOOKS!=='undefined'){
      const offer=_pickRandomOffers(cty,1)[0];
      if(offer){
        const hl=(HEADLINES[cat]||(()=>`Still deciding where to bet in ${cname}?`))(cname);
        return{
          id:'commercial',goal:'affiliate',
          headline:hl,
          bodyHtml:`<div data-ei-cta="commercial_offer" data-ei-goal="affiliate">${_offerCard(offer)}</div>`,
          secondaryHref:`/best-betting-in-${slug}/`,secondaryText:`See all bookmakers in ${cname} →`
        };
      }
    }

    // Default / fallback: alternate between a soft lead-gen ask (real Telegram
    // channel — there's no email/ESP backend on this static site, so a genuine
    // ongoing-value channel that actually exists stands in for "email capture")
    // and a plain compare CTA, decided once per popup since it only fires once
    // per session anyway.
    if(Math.random()<0.5){
      return{
        id:'social',goal:'lead',
        headline:'Before you go, get free tips daily',
        bodyHtml:'<p class="ei-sub">Join the SifuFinds Telegram channel for daily match tips and live odds updates. No spam, just picks.</p>',
        ctaText:'Get free tips on Telegram →',ctaHref:'https://t.me/sifufinds',ctaTarget:'_blank'
      };
    }
    return{
      id:'final',goal:'engagement',
      headline:`See today's best betting sites in ${cname}`,
      bodyHtml:'<p class="ei-sub">Compare verified bonuses and licensed bookmakers before you decide.</p>',
      ctaText:'See the best options →',ctaHref:`/best-betting-in-${slug}/`,ctaTarget:'_self'
    };
  }

  let lastFocused=null;

  function onKeydown(e){
    if(e.key==='Escape')dismiss('escape');
  }

  function trapFocus(card){
    card.addEventListener('keydown',function(e){
      if(e.key!=='Tab')return;
      const f=card.querySelectorAll('a[href],button:not([disabled])');
      if(!f.length)return;
      const first=f[0],last=f[f.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
    });
  }

  function open(trigger){
    trackEvent('exit_intent_detected',{trigger});
    const returning=isReturningVisitor();
    const exp=buildExperience();
    ssSet(_OFFER_POPUP_SS,'1'); // suppress showOfferPopup() for the rest of this session too
    lsSet(LS_LAST_SHOWN,String(Date.now()));
    lastFocused=document.activeElement;

    const el=document.createElement('div');
    el.id='exit-intent-bg';
    el.className='exit-intent-bg open';
    el.innerHTML=`<div class="exit-intent-card" role="dialog" aria-modal="true" aria-labelledby="ei-headline" tabindex="-1">
      <button class="exit-intent-close" id="ei-close" aria-label="Close">×</button>
      <div class="ei-eyebrow">${returning?'Welcome back':'Before you go'}</div>
      <h2 id="ei-headline">${exp.headline}</h2>
      ${exp.bodyHtml||''}
      ${exp.ctaText?`<a class="gbtn ei-cta" href="${exp.ctaHref}" target="${exp.ctaTarget||'_self'}"${exp.ctaTarget==='_blank'?` rel="noopener noreferrer${exp.goal==='affiliate'?' sponsored':''}"`:''} data-ei-cta="${exp.id}" data-ei-goal="${exp.goal}">${exp.ctaText}</a>`:''}
      ${exp.secondaryHref?`<a class="ei-secondary" href="${exp.secondaryHref}" data-ei-cta="${exp.id}_secondary">${exp.secondaryText}</a>`:''}
      <p class="ei-dis">18+ only. Bet responsibly. <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer">BeGambleAware.org</a></p>
    </div>`;
    document.body.appendChild(el);
    document.body.style.overflow='hidden';

    trackEvent('exit_intent_variant_viewed',{variant:exp.id});
    trackEvent('exit_intent_displayed',{variant:exp.id,trigger});

    el.addEventListener('click',function(e){
      if(e.target===el){dismiss('backdrop');return;}
      const cta=e.target.closest('[data-ei-cta]');
      if(cta){
        const goal=cta.dataset.eiGoal;
        trackEvent('exit_intent_cta_clicked',{variant:exp.id,ctaId:cta.dataset.eiCta});
        if(goal==='affiliate'||goal==='lead')trackEvent('exit_intent_converted',{variant:exp.id,ctaId:cta.dataset.eiCta});
      }
    });
    document.getElementById('ei-close').addEventListener('click',function(){dismiss('close_button');});
    document.addEventListener('keydown',onKeydown);

    const card=el.querySelector('.exit-intent-card');
    trapFocus(card);
    card.focus();
  }

  function dismiss(reason){
    const el=document.getElementById('exit-intent-bg');
    if(el)el.remove();
    document.body.style.overflow='';
    document.removeEventListener('keydown',onKeydown);
    lastModalCloseTs=Date.now();
    trackEvent('exit_intent_dismissed',{reason});
    if(lastFocused&&typeof lastFocused.focus==='function')lastFocused.focus();
  }
})();

// ── LANGUAGE (I18N) ────────────────────────────────────────────────────────────
// Client-side chrome translator: nav/footer/filters/disclaimers repeat verbatim
// across every page, so one dictionary + one DOM pass covers the whole site
// with no per-page edits. Page-specific prose (blog bodies, FAQ answers) is out
// of scope here — it needs real translated content, not a phrase swap.
const _LANGS=[
  {code:'en',label:'English',flag:'🇬🇧'},
  {code:'fr',label:'Français',flag:'🇫🇷'},
  {code:'de',label:'Deutsch',flag:'🇩🇪'},
  {code:'es',label:'Español',flag:'🇪🇸'},
  {code:'pt',label:'Português',flag:'🇵🇹'},
  {code:'sw',label:'Kiswahili',flag:'🇰🇪'}
];
const _LANG_LS='sf_lang';
// Default UI language per country — the visitor can always override via the switcher.
const COUNTRY_LANG={NG:'en',KE:'en',GH:'en',ZA:'en',TZ:'sw',UG:'en',ZM:'en',ET:'en',CI:'fr',CM:'fr',SN:'fr',RW:'fr',ZW:'en',MW:'en',MZ:'pt',AO:'pt',CD:'fr',BW:'en',NA:'en',EG:'en',MA:'fr',SL:'en',LR:'en'};

// Real translated pages (see gen_blog_post_pages.py) mark themselves with
// <html data-locale="fr">. That fixes the chrome language for *this page only* —
// it deliberately isn't persisted to localStorage, so following a link back to
// an English page doesn't leave the visitor's actual preference clobbered by
// a single article they happened to land on.
function _pageLocale(){
  const dl=document.documentElement.getAttribute('data-locale');
  return dl&&_LANGS.some(l=>l.code===dl&&l.code!=='en')?dl:null;
}
function getCurrentLang(){
  return new URLSearchParams(window.location.search).get('lang')
    ||_pageLocale()
    ||localStorage.getItem(_LANG_LS)
    ||COUNTRY_LANG[getCurrentCountry()]
    ||'en';
}
function changeLang(code){
  localStorage.setItem(_LANG_LS,code);
  // If this page declares a real translated version (hreflang alternate),
  // jump straight to it instead of just re-skinning the chrome on the same URL.
  const alt=document.querySelector(`link[rel="alternate"][hreflang="${code}"]`);
  if(alt){window.location.href=alt.href;return;}
  const u=new URL(window.location.href);
  u.searchParams.set('lang',code);
  window.location.href=u.toString();
}
function injectLangSelector(){
  const bar=document.querySelector('.tbar-r');
  if(!bar||document.getElementById('langSel'))return;
  const sel=document.createElement('select');
  sel.className='csel';
  sel.id='langSel';
  sel.setAttribute('aria-label','Language / Langue / Sprache / Idioma / Idioma / Lugha');
  sel.innerHTML=_LANGS.map(l=>`<option value="${l.code}">${l.flag} ${l.label}</option>`).join('');
  sel.value=getCurrentLang();
  sel.onchange=function(){changeLang(this.value);};
  bar.insertBefore(sel,bar.firstChild);
}
function syncLangUI(){
  const sel=document.getElementById('langSel');
  if(sel)sel.value=getCurrentLang();
}

// English source string -> translation per language. Keys must match a text
// node's *trimmed* content exactly (see applyI18n) so partial-sentence swaps
// inside unique page prose never happen by accident.
const I18N_UI={
'⭐ Best Bonuses':{fr:'⭐ Meilleurs Bonus',de:'⭐ Beste Boni',es:'⭐ Mejores Bonos',pt:'⭐ Melhores Bônus',sw:'⭐ Zawadi Bora'},
'💡 Tips':{fr:'💡 Pronostics',de:'💡 Tipps',es:'💡 Pronósticos',pt:'💡 Palpites',sw:'💡 Vidokezo'},
'🎰 Casino':{fr:'🎰 Casino',de:'🎰 Casino',es:'🎰 Casino',pt:'🎰 Cassino',sw:'🎰 Kasino'},
'📊 Live Odds':{fr:'📊 Cotes en Direct',de:'📊 Live-Quoten',es:'📊 Cuotas en Vivo',pt:'📊 Odds ao Vivo',sw:'📊 Vigezo vya Moja kwa Moja'},
'⚽ Leagues':{fr:'⚽ Ligues',de:'⚽ Ligen',es:'⚽ Ligas',pt:'⚽ Ligas',sw:'⚽ Ligi'},
'🌍 Countries':{fr:'🌍 Pays',de:'🌍 Länder',es:'🌍 Países',pt:'🌍 Países',sw:'🌍 Nchi'},
'📰 Blog':{fr:'📰 Blog',de:'📰 Blog',es:'📰 Blog',pt:'📰 Blog',sw:'📰 Blogu'},
'✉️ Contact':{fr:'✉️ Contact',de:'✉️ Kontakt',es:'✉️ Contacto',pt:'✉️ Contato',sw:'✉️ Wasiliana'},
'🏠 Home':{fr:'🏠 Accueil',de:'🏠 Startseite',es:'🏠 Inicio',pt:'🏠 Início',sw:'🏠 Nyumbani'},
'🌍 Africa':{fr:'🌍 Afrique',de:'🌍 Afrika',es:'🌍 África',pt:'🌍 África',sw:'🌍 Afrika'},
'Responsible Gambling':{fr:'Jeu Responsable',de:'Verantwortungsvolles Spielen',es:'Juego Responsable',pt:'Jogo Responsável',sw:'Kamari yenye Uwajibikaji'},
'18+ Only':{fr:'18 ans et +',de:'Nur 18+',es:'Solo 18+',pt:'Apenas 18+',sw:'Miaka 18+ Pekee'},
'Your Country:':{fr:'Votre pays :',de:'Ihr Land:',es:'Tu país:',pt:'Seu país:',sw:'Nchi Yako:'},
'Search bookmakers...':{fr:'Rechercher un bookmaker...',de:'Wettanbieter suchen...',es:'Buscar casas de apuestas...',pt:'Buscar casas de apostas...',sw:'Tafuta kampuni za kubeti...'},
'✅ Licensed & Verified':{fr:'✅ Agréé et Vérifié',de:'✅ Lizenziert & Geprüft',es:'✅ Licenciado y Verificado',pt:'✅ Licenciado e Verificado',sw:'✅ Ina Leseni na Imethibitishwa'},
'📱 Mobile-First':{fr:'📱 Optimisé Mobile',de:'📱 Mobil-Optimiert',es:'📱 Optimizado para Móvil',pt:'📱 Otimizado para Celular',sw:'📱 Rafiki wa Simu'},
'🔄 Updated Daily':{fr:'🔄 Mis à Jour Chaque Jour',de:'🔄 Täglich Aktualisiert',es:'🔄 Actualizado a Diario',pt:'🔄 Atualizado Diariamente',sw:'🔄 Inasasishwa Kila Siku'},
'💳 Local Payments':{fr:'💳 Paiements Locaux',de:'💳 Lokale Zahlungen',es:'💳 Pagos Locales',pt:'💳 Pagamentos Locais',sw:'💳 Malipo ya Ndani'},
'largest welcome bonus':{fr:'plus gros bonus de bienvenue',de:'größter Willkommensbonus',es:'mayor bono de bienvenida',pt:'maior bônus de boas-vindas',sw:'zawadi kubwa zaidi ya kujiunga'},
'licensed bookmakers':{fr:'bookmakers agréés',de:'lizenzierte Wettanbieter',es:'casas de apuestas licenciadas',pt:'casas de apostas licenciadas',sw:'kampuni za kubeti zenye leseni'},
'last updated':{fr:'dernière mise à jour',de:'zuletzt aktualisiert',es:'última actualización',pt:'última atualização',sw:'ilisasishwa mara ya mwisho'},
'⭐ Top Picks ·':{fr:'⭐ Meilleurs Choix ·',de:'⭐ Top-Auswahl ·',es:'⭐ Mejores Opciones ·',pt:'⭐ Melhores Escolhas ·',sw:'⭐ Chaguo Bora ·'},
'📢 Advertiser Disclosure: We may earn commission from bookmaker links. All bonuses independently verified. Always check the bookmaker\'s official site for current T&Cs.':{
  fr:'📢 Avis publicitaire : Nous pouvons percevoir une commission sur les liens des bookmakers. Tous les bonus sont vérifiés indépendamment. Consultez toujours le site officiel du bookmaker pour les conditions en vigueur.',
  de:'📢 Werbehinweis: Wir können eine Provision über Wettanbieter-Links verdienen. Alle Boni werden unabhängig geprüft. Prüfen Sie stets die offizielle Website des Anbieters für aktuelle Bedingungen.',
  es:'📢 Divulgación publicitaria: Podemos recibir comisión por los enlaces a casas de apuestas. Todos los bonos se verifican de forma independiente. Consulta siempre el sitio oficial de la casa de apuestas para conocer los términos vigentes.',
  pt:'📢 Divulgação de publicidade: Podemos receber comissão pelos links das casas de apostas. Todos os bônus são verificados de forma independente. Consulte sempre o site oficial da casa de apostas para os termos atuais.',
  sw:'📢 Ufichuzi wa Matangazo: Tunaweza kupata kamisheni kutoka kwa viungo vya kampuni za kubeti. Zawadi zote zimethibitishwa kwa uhuru. Daima angalia tovuti rasmi ya kampuni ya kubeti kwa masharti ya sasa.'},
'How We Rank the Best Betting Sites in Africa':{fr:'Comment Nous Classons les Meilleurs Sites de Paris en Afrique',de:'Wie Wir die Besten Wettseiten Afrikas Bewerten',es:'Cómo Clasificamos los Mejores Sitios de Apuestas en África',pt:'Como Classificamos os Melhores Sites de Apostas na África',sw:'Jinsi Tunavyopanga Tovuti Bora za Kubeti Afrika'},
'Every bookmaker listed on SifuFinds is scored across four factors, not just bonus size:':{
  fr:'Chaque bookmaker répertorié sur SifuFinds est noté selon quatre critères, pas seulement la taille du bonus :',
  de:'Jeder auf SifuFinds gelistete Wettanbieter wird nach vier Kriterien bewertet, nicht nur nach der Bonushöhe:',
  es:'Cada casa de apuestas listada en SifuFinds se puntúa según cuatro factores, no solo el tamaño del bono:',
  pt:'Cada casa de apostas listada no SifuFinds é avaliada em quatro fatores, não apenas o tamanho do bônus:',
  sw:'Kila kampuni ya kubeti iliyoorodheshwa kwenye SifuFinds inapimwa kwa vigezo vinne, si ukubwa wa zawadi tu:'},
'🛡️ Licensing & Trust':{fr:'🛡️ Licence et Confiance',de:'🛡️ Lizenz & Vertrauen',es:'🛡️ Licencia y Confianza',pt:'🛡️ Licença e Confiança',sw:'🛡️ Leseni na Uaminifu'},
'Only operators licensed by a recognised African regulator (NLRC, BCLB, GCA, WCGRB and others) are listed.':{
  fr:'Seuls les opérateurs agréés par un régulateur africain reconnu (NLRC, BCLB, GCA, WCGRB, etc.) sont répertoriés.',
  de:'Nur Anbieter mit Lizenz einer anerkannten afrikanischen Aufsichtsbehörde (NLRC, BCLB, GCA, WCGRB u. a.) werden gelistet.',
  es:'Solo se incluyen operadores licenciados por un regulador africano reconocido (NLRC, BCLB, GCA, WCGRB y otros).',
  pt:'Somente operadores licenciados por um regulador africano reconhecido (NLRC, BCLB, GCA, WCGRB e outros) são listados.',
  sw:'Waendeshaji walio na leseni kutoka kwa mdhibiti wa Kiafrika anayetambulika (NLRC, BCLB, GCA, WCGRB na wengine) pekee ndio wameorodheshwa.'},
'📊 Odds Quality':{fr:'📊 Qualité des Cotes',de:'📊 Quotenqualität',es:'📊 Calidad de Cuotas',pt:'📊 Qualidade das Odds',sw:'📊 Ubora wa Vigezo'},
'How competitive a bookmaker\'s odds are on African football, CAF competitions, and major global leagues.':{
  fr:'À quel point les cotes d\'un bookmaker sont compétitives sur le football africain, les compétitions de la CAF et les grands championnats mondiaux.',
  de:'Wie wettbewerbsfähig die Quoten eines Anbieters bei afrikanischem Fußball, CAF-Wettbewerben und großen internationalen Ligen sind.',
  es:'Qué tan competitivas son las cuotas de una casa de apuestas en el fútbol africano, las competiciones de la CAF y las principales ligas mundiales.',
  pt:'O quão competitivas são as odds de uma casa de apostas no futebol africano, competições da CAF e principais ligas mundiais.',
  sw:'Jinsi vigezo vya kampuni ya kubeti vinavyoshindana katika soka la Afrika, mashindano ya CAF, na ligi kuu za dunia.'},
'⚡ Payout Speed':{fr:'⚡ Rapidité des Paiements',de:'⚡ Auszahlungsgeschwindigkeit',es:'⚡ Velocidad de Pago',pt:'⚡ Velocidade de Pagamento',sw:'⚡ Kasi ya Malipo'},
'How quickly verified withdrawals process via local payment methods like OPay, M-Pesa, and MTN MoMo.':{
  fr:'La rapidité de traitement des retraits vérifiés via des moyens de paiement locaux comme OPay, M-Pesa et MTN MoMo.',
  de:'Wie schnell verifizierte Auszahlungen über lokale Zahlungsmethoden wie OPay, M-Pesa und MTN MoMo abgewickelt werden.',
  es:'Qué tan rápido se procesan los retiros verificados a través de métodos de pago locales como OPay, M-Pesa y MTN MoMo.',
  pt:'A rapidez com que os saques verificados são processados via métodos de pagamento locais como OPay, M-Pesa e MTN MoMo.',
  sw:'Jinsi utoaji fedha ulioidhinishwa unavyochakatwa haraka kupitia njia za malipo za ndani kama OPay, M-Pesa, na MTN MoMo.'},
'🎁 Welcome Bonus':{fr:'🎁 Bonus de Bienvenue',de:'🎁 Willkommensbonus',es:'🎁 Bono de Bienvenida',pt:'🎁 Bônus de Boas-Vindas',sw:'🎁 Zawadi ya Kujiunga'},
'Real, verified sign-up offers and ongoing promotions — one factor among several, not the only one.':{
  fr:'Des offres d\'inscription réelles et vérifiées ainsi que des promotions continues — un critère parmi d\'autres, pas le seul.',
  de:'Echte, geprüfte Anmeldeangebote und laufende Aktionen — ein Faktor unter mehreren, nicht der einzige.',
  es:'Ofertas de registro reales y verificadas, y promociones continuas: un factor entre varios, no el único.',
  pt:'Ofertas de cadastro reais e verificadas, além de promoções contínuas — um fator entre vários, não o único.',
  sw:'Ofa halisi, zilizothibitishwa za kujisajili na matangazo yanayoendelea — ni kigezo kimoja kati ya vingi, si pekee.'},
'Showing':{fr:'Affichage',de:'Anzeige',es:'Mostrando',pt:'Mostrando',sw:'Inaonyesha'},
'bookmakers':{fr:'bookmakers',de:'Wettanbieter',es:'casas de apuestas',pt:'casas de apostas',sw:'kampuni za kubeti'},
'· Use dropdown above or quick-switch below':{fr:'· Utilisez le menu ci-dessus ou les raccourcis ci-dessous',de:'· Nutzen Sie das Menü oben oder die Schnellauswahl unten',es:'· Usa el menú de arriba o el acceso rápido de abajo',pt:'· Use o menu acima ou a troca rápida abaixo',sw:'· Tumia menyu iliyo juu au ubadilishaji wa haraka hapa chini'},
'Sort:':{fr:'Trier :',de:'Sortieren:',es:'Ordenar:',pt:'Ordenar:',sw:'Panga:'},
'Editors\' Picks':{fr:'Sélection de la Rédaction',de:'Redaktionsauswahl',es:'Selección del Editor',pt:'Seleção do Editor',sw:'Chaguo za Wahariri'},
'Highest Rated':{fr:'Mieux Notés',de:'Bestbewertet',es:'Mejor Valorados',pt:'Mais Bem Avaliados',sw:'Zilizopimwa Juu Zaidi'},
'Highest Bonus':{fr:'Bonus le Plus Élevé',de:'Höchster Bonus',es:'Mayor Bono',pt:'Maior Bônus',sw:'Zawadi Kubwa Zaidi'},
'Most Sports':{fr:'Plus de Sports',de:'Meiste Sportarten',es:'Más Deportes',pt:'Mais Esportes',sw:'Michezo Mingi Zaidi'},
'Filter:':{fr:'Filtrer :',de:'Filtern:',es:'Filtrar:',pt:'Filtrar:',sw:'Chuja:'},
'All':{fr:'Tous',de:'Alle',es:'Todos',pt:'Todos',sw:'Zote'},
'No Deposit':{fr:'Sans Dépôt',de:'Ohne Einzahlung',es:'Sin Depósito',pt:'Sem Depósito',sw:'Bila Amana'},
'Cash Out':{fr:'Cash Out',de:'Cash Out',es:'Cash Out',pt:'Cash Out',sw:'Cash Out'},
'Live Stream':{fr:'Diffusion en Direct',de:'Live-Stream',es:'Transmisión en Vivo',pt:'Transmissão ao Vivo',sw:'Utiririshaji wa Moja kwa Moja'},
'Instant Pay':{fr:'Paiement Instantané',de:'Sofortzahlung',es:'Pago Instantáneo',pt:'Pagamento Instantâneo',sw:'Malipo ya Papo Hapo'},
'M-Pesa':{fr:'M-Pesa',de:'M-Pesa',es:'M-Pesa',pt:'M-Pesa',sw:'M-Pesa'},
'MTN MoMo':{fr:'MTN MoMo',de:'MTN MoMo',es:'MTN MoMo',pt:'MTN MoMo',sw:'MTN MoMo'},
'⚠️ Gambling involves risk. Only bet what you can afford to lose.':{
  fr:'⚠️ Les paris comportent des risques. Ne pariez que ce que vous pouvez vous permettre de perdre.',
  de:'⚠️ Wetten sind mit Risiko verbunden. Setzen Sie nur, was Sie sich zu verlieren leisten können.',
  es:'⚠️ Apostar implica riesgo. Apuesta solo lo que puedas permitirte perder.',
  pt:'⚠️ Apostar envolve risco. Aposte apenas o que você pode perder.',
  sw:'⚠️ Kubeti kuna hatari. Weka dau kiasi unachoweza kumudu kupoteza.'},
'GamCare':{fr:'GamCare',de:'GamCare',es:'GamCare',pt:'GamCare',sw:'GamCare'},
'BeGambleAware':{fr:'BeGambleAware',de:'BeGambleAware',es:'BeGambleAware',pt:'BeGambleAware',sw:'BeGambleAware'},
'NCPG Africa':{fr:'NCPG Afrique',de:'NCPG Afrika',es:'NCPG África',pt:'NCPG África',sw:'NCPG Afrika'},
'18+ only.':{fr:'18 ans et + uniquement.',de:'Nur 18+.',es:'Solo mayores de 18.',pt:'Apenas 18+.',sw:'Miaka 18+ pekee.'},
'Compare:':{fr:'Comparer :',de:'Vergleichen:',es:'Comparar:',pt:'Comparar:',sw:'Linganisha:'},
'Compare Now →':{fr:'Comparer Maintenant →',de:'Jetzt Vergleichen →',es:'Comparar Ahora →',pt:'Comparar Agora →',sw:'Linganisha Sasa →'},
'Clear':{fr:'Effacer',de:'Löschen',es:'Borrar',pt:'Limpar',sw:'Futa'},
'Compare Sports Betting Bonuses — Side by Side':{fr:'Comparer les Bonus de Paris Sportifs — Côte à Côte',de:'Sportwetten-Boni Vergleichen — Nebeneinander',es:'Comparar Bonos de Apuestas Deportivas — Lado a Lado',pt:'Comparar Bônus de Apostas Esportivas — Lado a Lado',sw:'Linganisha Zawadi za Kubeti Michezo — Bega kwa Bega'},
'Bonuses':{fr:'Bonus',de:'Boni',es:'Bonos',pt:'Bônus',sw:'Zawadi'},
'Payments':{fr:'Paiements',de:'Zahlungen',es:'Pagos',pt:'Pagamentos',sw:'Malipo'},
'Tips':{fr:'Pronostics',de:'Tipps',es:'Pronósticos',pt:'Palpites',sw:'Vidokezo'},
'Countries':{fr:'Pays',de:'Länder',es:'Países',pt:'Países',sw:'Nchi'},
'More Countries':{fr:'Plus de Pays',de:'Weitere Länder',es:'Más Países',pt:'Mais Países',sw:'Nchi Zaidi'},
'Odds':{fr:'Cotes',de:'Quoten',es:'Cuotas',pt:'Odds',sw:'Vigezo'},
'Guides':{fr:'Guides',de:'Ratgeber',es:'Guías',pt:'Guias',sw:'Miongozo'},
'Free Tools':{fr:'Outils Gratuits',de:'Kostenlose Tools',es:'Herramientas Gratis',pt:'Ferramentas Grátis',sw:'Zana za Bure'},
'About':{fr:'À Propos',de:'Über Uns',es:'Acerca de',pt:'Sobre',sw:'Kuhusu'},
'Best Bonuses':{fr:'Meilleurs Bonus',de:'Beste Boni',es:'Mejores Bonos',pt:'Melhores Bônus',sw:'Zawadi Bora'},
'No Deposit Bonus':{fr:'Bonus Sans Dépôt',de:'Bonus Ohne Einzahlung',es:'Bono Sin Depósito',pt:'Bônus Sem Depósito',sw:'Zawadi Bila Amana'},
'Cash Out Sites':{fr:'Sites avec Cash Out',de:'Cash-Out-Seiten',es:'Sitios con Cash Out',pt:'Sites com Cash Out',sw:'Tovuti za Cash Out'},
'Live Streaming':{fr:'Diffusion en Direct',de:'Live-Streaming',es:'Transmisión en Vivo',pt:'Transmissão ao Vivo',sw:'Utiririshaji wa Moja kwa Moja'},
'M-Pesa Betting':{fr:'Paris M-Pesa',de:'M-Pesa Wetten',es:'Apuestas M-Pesa',pt:'Apostas M-Pesa',sw:'Kubeti kwa M-Pesa'},
'MTN MoMo Betting':{fr:'Paris MTN MoMo',de:'MTN MoMo Wetten',es:'Apuestas MTN MoMo',pt:'Apostas MTN MoMo',sw:'Kubeti kwa MTN MoMo'},
'Instant Pay Sites':{fr:'Sites à Paiement Instantané',de:'Sofortzahlungs-Seiten',es:'Sitios de Pago Instantáneo',pt:'Sites de Pagamento Instantâneo',sw:'Tovuti za Malipo ya Papo Hapo'},
'Free Tips Today':{fr:'Pronostics Gratuits du Jour',de:'Kostenlose Tipps Heute',es:'Pronósticos Gratis de Hoy',pt:'Palpites Grátis de Hoje',sw:'Vidokezo vya Bure Leo'},
'AFCON Tips':{fr:'Pronostics CAN',de:'AFCON-Tipps',es:'Pronósticos CAN',pt:'Palpites CAN',sw:'Vidokezo vya AFCON'},
'CAF CL Tips':{fr:'Pronostics Ligue des Champions CAF',de:'CAF-CL-Tipps',es:'Pronósticos Liga de Campeones CAF',pt:'Palpites Liga dos Campeões CAF',sw:'Vidokezo vya CAF CL'},
'Best Casinos':{fr:'Meilleurs Casinos',de:'Beste Casinos',es:'Mejores Casinos',pt:'Melhores Cassinos',sw:'Kasino Bora'},
'No Deposit Casino':{fr:'Casino Sans Dépôt',de:'Casino Ohne Einzahlung',es:'Casino Sin Depósito',pt:'Cassino Sem Depósito',sw:'Kasino Bila Amana'},
'Live Casino':{fr:'Casino en Direct',de:'Live-Casino',es:'Casino en Vivo',pt:'Cassino ao Vivo',sw:'Kasino ya Moja kwa Moja'},
'Jackpots':{fr:'Jackpots',de:'Jackpots',es:'Jackpots',pt:'Jackpots',sw:'Jackpot'},
'All Leagues':{fr:'Toutes les Ligues',de:'Alle Ligen',es:'Todas las Ligas',pt:'Todas as Ligas',sw:'Ligi Zote'},
'CAF CL Odds':{fr:'Cotes Ligue des Champions CAF',de:'CAF-CL-Quoten',es:'Cuotas Liga de Campeones CAF',pt:'Odds Liga dos Campeões CAF',sw:'Vigezo vya CAF CL'},
'AFCON Odds':{fr:'Cotes CAN',de:'AFCON-Quoten',es:'Cuotas CAN',pt:'Odds CAN',sw:'Vigezo vya AFCON'},
'Premier League':{fr:'Premier League',de:'Premier League',es:'Premier League',pt:'Premier League',sw:'Premier League'},
'How to Bet on Football':{fr:'Comment Parier sur le Football',de:'Wie Man auf Fußball Wettet',es:'Cómo Apostar en Fútbol',pt:'Como Apostar em Futebol',sw:'Jinsi ya Kubeti Soka'},
'What is an Accumulator?':{fr:'Qu\'est-ce qu\'un Pari Combiné ?',de:'Was ist eine Kombiwette?',es:'¿Qué es una Apuesta Combinada?',pt:'O que é uma Aposta Múltipla?',sw:'Accumulator ni Nini?'},
'M-Pesa Betting Sites':{fr:'Sites de Paris M-Pesa',de:'M-Pesa Wettseiten',es:'Sitios de Apuestas M-Pesa',pt:'Sites de Apostas M-Pesa',sw:'Tovuti za Kubeti za M-Pesa'},
'No Deposit Bonuses':{fr:'Bonus Sans Dépôt',de:'Boni Ohne Einzahlung',es:'Bonos Sin Depósito',pt:'Bônus Sem Depósito',sw:'Zawadi Bila Amana'},
'World Cup 2026 Tips':{fr:'Pronostics Coupe du Monde 2026',de:'WM-2026-Tipps',es:'Pronósticos Mundial 2026',pt:'Palpites Copa do Mundo 2026',sw:'Vidokezo vya Kombe la Dunia 2026'},
'World Cup 2026':{fr:'Coupe du Monde 2026',de:'WM 2026',es:'Mundial 2026',pt:'Copa do Mundo 2026',sw:'Kombe la Dunia 2026'},
'Odds Calculator':{fr:'Calculateur de Cotes',de:'Quotenrechner',es:'Calculadora de Cuotas',pt:'Calculadora de Odds',sw:'Kikokotoo cha Vigezo'},
'Parlay Calculator':{fr:'Calculateur de Paris Combinés',de:'Kombiwetten-Rechner',es:'Calculadora de Combinadas',pt:'Calculadora de Múltiplas',sw:'Kikokotoo cha Parlay'},
'Press & Media Kit':{fr:'Kit Presse et Médias',de:'Presse- & Medienkit',es:'Kit de Prensa y Medios',pt:'Kit de Imprensa e Mídia',sw:'Kifurushi cha Vyombo vya Habari'},
'About SifuFinds':{fr:'À Propos de SifuFinds',de:'Über SifuFinds',es:'Acerca de SifuFinds',pt:'Sobre o SifuFinds',sw:'Kuhusu SifuFinds'},
'Contact Us':{fr:'Nous Contacter',de:'Kontaktieren Sie Uns',es:'Contáctanos',pt:'Fale Conosco',sw:'Wasiliana Nasi'},
'Privacy Policy':{fr:'Politique de Confidentialité',de:'Datenschutzrichtlinie',es:'Política de Privacidad',pt:'Política de Privacidade',sw:'Sera ya Faragha'},
'Home':{fr:'Accueil',de:'Startseite',es:'Inicio',pt:'Início',sw:'Nyumbani'},
'Blog':{fr:'Blog',de:'Blog',es:'Blog',pt:'Blog',sw:'Blogu'},
'Bookmakers':{fr:'Bookmakers',de:'Wettanbieter',es:'Casas de Apuestas',pt:'Casas de Apostas',sw:'Kampuni za Kubeti'},
'Compare Bookmakers — Start Betting Today':{fr:'Comparer les Bookmakers — Commencez à Parier Aujourd\'hui',de:'Wettanbieter Vergleichen — Heute Loslegen',es:'Comparar Casas de Apuestas — Empieza a Apostar Hoy',pt:'Comparar Casas de Apostas — Comece a Apostar Hoje',sw:'Linganisha Kampuni za Kubeti — Anza Kubeti Leo'},
'Compare All Bookmakers →':{fr:'Comparer Tous les Bookmakers →',de:'Alle Wettanbieter Vergleichen →',es:'Comparar Todas las Casas →',pt:'Comparar Todas as Casas →',sw:'Linganisha Kampuni Zote →'},
'📢 Advertiser Disclosure: SifuFinds may earn commission from bookmaker links. All bonuses verified. 18+.':{
  fr:'📢 Avis publicitaire : SifuFinds peut percevoir une commission sur les liens des bookmakers. Tous les bonus sont vérifiés. 18 ans et +.',
  de:'📢 Werbehinweis: SifuFinds kann eine Provision über Wettanbieter-Links verdienen. Alle Boni geprüft. Nur 18+.',
  es:'📢 Divulgación publicitaria: SifuFinds puede recibir comisión por los enlaces a casas de apuestas. Todos los bonos verificados. Solo 18+.',
  pt:'📢 Divulgação de publicidade: o SifuFinds pode receber comissão pelos links das casas de apostas. Todos os bônus verificados. Apenas 18+.',
  sw:'📢 Ufichuzi wa Matangazo: SifuFinds inaweza kupata kamisheni kutoka kwa viungo vya kampuni za kubeti. Zawadi zote zimethibitishwa. Miaka 18+ pekee.'},
'⚠️ Gambling involves risk. Only bet what you can afford to lose. 18+ only. If gambling is causing harm, seek help.':{
  fr:'⚠️ Les paris comportent des risques. Ne pariez que ce que vous pouvez vous permettre de perdre. 18 ans et + uniquement. Si le jeu vous cause du tort, demandez de l\'aide.',
  de:'⚠️ Wetten sind mit Risiko verbunden. Setzen Sie nur, was Sie sich zu verlieren leisten können. Nur 18+. Wenn Glücksspiel Schaden verursacht, holen Sie sich Hilfe.',
  es:'⚠️ Apostar implica riesgo. Apuesta solo lo que puedas permitirte perder. Solo mayores de 18. Si el juego te está causando daño, busca ayuda.',
  pt:'⚠️ Apostar envolve risco. Aposte apenas o que você pode perder. Apenas 18+. Se o jogo estiver causando danos, procure ajuda.',
  sw:'⚠️ Kubeti kuna hatari. Weka dau kiasi unachoweza kumudu kupoteza. Miaka 18+ pekee. Ikiwa kamari inasababisha madhara, tafuta msaada.'}
};

function applyI18n(lang){
  lang=lang||getCurrentLang();
  document.documentElement.lang=lang;
  if(lang==='en')return;
  const dict=I18N_UI;
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{
    acceptNode(node){
      const p=node.parentElement;
      if(!p)return NodeFilter.FILTER_REJECT;
      const tag=p.tagName;
      if(tag==='SCRIPT'||tag==='STYLE'||tag==='NOSCRIPT'||tag==='TEXTAREA')return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  const nodes=[];
  let n;
  while(n=walker.nextNode())nodes.push(n);
  nodes.forEach(node=>{
    const raw=node.nodeValue;
    const trimmed=raw.trim();
    if(!trimmed)return;
    const entry=dict[trimmed];
    if(entry&&entry[lang])node.nodeValue=raw.replace(trimmed,entry[lang]);
  });
  document.querySelectorAll('[placeholder],[aria-label],[title]').forEach(el=>{
    ['placeholder','aria-label','title'].forEach(attr=>{
      const v=el.getAttribute(attr);
      const entry=v&&dict[v];
      if(entry&&entry[lang])el.setAttribute(attr,entry[lang]);
    });
  });
}

// Runs once the static chrome for this page has parsed (shared.js sits at the
// bottom of <body>, so everything above it — nav, topbar, footer — is already
// in the DOM). A second pass on window 'load' catches anything a page's own
// init() renders afterwards.
injectLangSelector();
applyI18n();
syncLangUI();
window.addEventListener('load',function(){applyI18n();syncLangUI();});
