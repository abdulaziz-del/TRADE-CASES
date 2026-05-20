"""
WTO Dispute Intelligence Platform
===================================
Backend: Flask + Anthropic AI + WTO Official Data
Data Source: WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)
             + Curated Saudi-relevant cases dataset
"""

import os
import json
import re
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, template_folder=".", static_folder=".")
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════════════════════
# DATASET A: Curated Saudi-Relevant Cases (Original Hand-Crafted Dataset)
# ══════════════════════════════════════════════════════════════════════════════
WTO_SAUDI_CASES = [
    {"ds_number":"DS627","title":"European Union — Carbon Border Adjustment Mechanism (CBAM)","complainant":"India","respondent":"European Union","third_parties":["China","Saudi Arabia","Brazil","Russia"],"agreements":["GATT 1994","SCM Agreement","TBT Agreement"],"articles":["Art. I","Art. III","Art. XX"],"subject":"Carbon Border Tax / Environment / Industrial Goods","sector":"Energy & Environment","year":2023,"status":"Consultations","stage":"Consultations","saudi_relevance":"HIGH","saudi_impact":"تأثير مباشر على صادرات البتروكيماويات والصلب السعودية إلى السوق الأوروبية","request_date":"2023-07-12","summary_ar":"تطعن الهند في آلية تعديل حدود الكربون الأوروبية (CBAM) التي تفرض رسوماً على الكربون على الواردات من قطاعات مثل الصلب والأسمنت والألمنيوم والأسمدة، مما يؤثر بشكل مباشر على صادرات المملكة العربية السعودية.","summary_en":"India challenges the EU's Carbon Border Adjustment Mechanism (CBAM) imposing carbon levies on imports from sectors like steel, cement, aluminum, fertilizers — directly affecting Saudi Arabia's exports.","keywords":["CBAM","carbon","environment","steel","aluminum","fertilizers","petrochemicals"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS590","title":"Saudi Arabia — Measures Concerning Trade in Goods and Services","complainant":"Qatar","respondent":"Saudi Arabia","third_parties":["United States","European Union","China"],"agreements":["GATT 1994","GATS"],"articles":["Art. I GATT","Art. V GATS","Art. XVII GATS"],"subject":"Trade Embargo / Services / Market Access","sector":"Services & Trade","year":2018,"status":"Panel Report issued","stage":"Compliance","saudi_relevance":"HIGH","saudi_impact":"المملكة طرف مدعى عليه — التزامات GATT/GATS، العلاقات التجارية الإقليمية","request_date":"2018-07-04","summary_ar":"طعنت قطر في الإجراءات السعودية المتعلقة بتجارة السلع والخدمات في إطار الحصار.","summary_en":"Qatar challenged Saudi measures on goods and services trade during the blockade. One of Saudi Arabia's most prominent WTO cases.","keywords":["blockade","embargo","GATS","services","Qatar"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS566","title":"United States — Certain Measures on Steel and Aluminum Products","complainant":"China","respondent":"United States","third_parties":["Saudi Arabia","EU","Japan","India"],"agreements":["GATT 1994","Safeguards Agreement"],"articles":["Art. XIX GATT","Art. 2 Safeguards"],"subject":"Steel / Aluminum / Section 232 / National Security","sector":"Metals & Mining","year":2018,"status":"Panel Report adopted","stage":"Implementation","saudi_relevance":"HIGH","saudi_impact":"المملكة شاركت كطرف ثالث؛ سابقة مهمة لقطاع الصلب السعودي","request_date":"2018-07-16","summary_ar":"طعنت الصين في التدابير الأمريكية على الصلب والألمنيوم استناداً إلى الأمن القومي. شاركت المملكة كطرف ثالث.","summary_en":"China challenges US Section 232 steel/aluminum tariffs. Saudi Arabia participated as third party. Key precedent for national security exceptions.","keywords":["steel","aluminum","section 232","national security","safeguards"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS579","title":"Saudi Arabia — Measures Concerning the Protection of Intellectual Property Rights","complainant":"Qatar","respondent":"Saudi Arabia","third_parties":["United States","European Union"],"agreements":["TRIPS Agreement"],"articles":["Art. 42","Art. 61"],"subject":"Intellectual Property / Broadcasting / beoutQ","sector":"Intellectual Property","year":2018,"status":"Panel established","stage":"Panel","saudi_relevance":"HIGH","saudi_impact":"المملكة طرف مدعى عليه — التزامات TRIPS وحماية الملكية الفكرية","request_date":"2018-04-04","summary_ar":"تطعن قطر في الإجراءات السعودية المتعلقة بحماية حقوق الملكية الفكرية، ولا سيما قضية beoutQ.","summary_en":"Qatar challenges Saudi measures regarding IP protection, specifically the beoutQ broadcasting piracy matter under TRIPS.","keywords":["TRIPS","IP","broadcasting","piracy","Qatar","beoutQ"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS510","title":"United States — Certain Measures Relating to the Renewable Energy Sector","complainant":"India","respondent":"United States","third_parties":["EU","Japan","China","Saudi Arabia"],"agreements":["SCM Agreement","GATT 1994"],"articles":["Art. 3 SCM","Art. III GATT"],"subject":"Renewable Energy / Subsidies / Solar Panels","sector":"Renewable Energy","year":2016,"status":"Panel Report adopted","stage":"Implementation","saudi_relevance":"MEDIUM","saudi_impact":"سابقة لدعم الطاقة المتجددة — ذات صلة ببرامج رؤية 2030 السعودية","request_date":"2016-09-09","summary_ar":"طعنت الهند في تدابير الطاقة المتجددة الأمريكية. سابقة مهمة لبرامج دعم الطاقة المتجددة في رؤية 2030.","summary_en":"India challenged US renewable energy measures. Important precedent for renewable energy subsidy programs relevant to Saudi Vision 2030.","keywords":["renewable energy","solar","subsidies","SCM","Vision 2030"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS598","title":"EU — Anti-Dumping Measures on Imports of Certain Fatty Alcohols","complainant":"Indonesia","respondent":"European Union","third_parties":["Malaysia","Saudi Arabia"],"agreements":["Anti-Dumping Agreement","GATT 1994"],"articles":["Art. 2","Art. 3","Art. 6"],"subject":"Anti-Dumping / Fatty Alcohols / Petrochemicals","sector":"Petrochemicals","year":2019,"status":"AB Report adopted","stage":"Completed","saudi_relevance":"MEDIUM","saudi_impact":"المملكة طرف ثالث — ذات صلة بصناعة البتروكيماويات وتدابير مكافحة الإغراق","request_date":"2019-10-02","summary_ar":"طعنت إندونيسيا في تدابير مكافحة الإغراق الأوروبية على الكحولات الدهنية.","summary_en":"Indonesia challenged EU anti-dumping on fatty alcohols. Saudi Arabia third party given petrochemical interests.","keywords":["anti-dumping","fatty alcohols","petrochemicals"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS591","title":"United Arab Emirates — Measures Relating to Trade in Goods and Services","complainant":"Qatar","respondent":"United Arab Emirates","third_parties":["Saudi Arabia","USA","EU"],"agreements":["GATT 1994","GATS"],"articles":["Art. I GATT","Art. II GATS"],"subject":"Trade Embargo / GCC / Services","sector":"Services & Trade","year":2018,"status":"Panel Report issued","stage":"Compliance","saudi_relevance":"HIGH","saudi_impact":"المملكة طرف ثالث؛ يؤثر على العلاقات التجارية الخليجية والسوابق الإقليمية","request_date":"2018-07-31","summary_ar":"طعنت قطر في الإجراءات الإماراتية. شاركت المملكة كطرف ثالث.","summary_en":"Qatar challenged UAE measures. Saudi Arabia third party. Important for Gulf regional trade precedents.","keywords":["UAE","GCC","blockade","GATS","Gulf"],"source":"WTO Saudi Cases Dataset"},
    {"ds_number":"DS543","title":"United States — Tariff Measures on Certain Goods from China","complainant":"China","respondent":"United States","third_parties":["EU","Japan","India","Saudi Arabia"],"agreements":["GATT 1994","Anti-Dumping Agreement"],"articles":["Art. I GATT","Art. II GATT"],"subject":"Section 301 Tariffs / Technology / Trade War","sector":"Technology & Manufacturing","year":2018,"status":"Panel Report adopted","stage":"Implementation","saudi_relevance":"MEDIUM","saudi_impact":"التوترات التجارية US-China تؤثر على سلاسل الإمداد وممرات التجارة السعودية","request_date":"2018-04-04","summary_ar":"طعنت الصين في الرسوم الأمريكية بموجب المادة 301. التوترات تؤثر على سلاسل الإمداد السعودية.","summary_en":"China challenged US Section 301 tariffs. US-China trade tensions affect Saudi trade corridors.","keywords":["Section 301","tariffs","trade war","China","supply chains"],"source":"WTO Saudi Cases Dataset"},
]


# ══════════════════════════════════════════════════════════════════════════════
# DATASET B: WTO Official Publication 1995-2022 (186 cases from PDF)
# Source: "WTO Dispute Settlement: One-Page Case Summaries 1995-2022"
# ══════════════════════════════════════════════════════════════════════════════
WTO_PDF_DISPUTES = [{"ds_number": "DS2", "title": "US – GASOLINE", "complainant": "Brazil, Venezuela", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. III and XX"], "articles": [], "subject": "The “Gasoline Rule” under the US Clean Air Act that set out the rules for establishing baseline figu", "sector": "Energy & Environment", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Energy & Environment السعودي — تستحق المتابعة", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure treated imported gasoline “less favourably” than domestic gasoline in violation of Art. III:4, as imported gasoline effectively experienced less favourable sales conditions than those afforded to domestic gasoline. In particular, under the regulation, importers had to adapt to an average standard, i.e. “statutory baseline”, that had no connection to the particular gasoline imported, while refiners of domestic gasoline had only to meet a standard linked to their own product in 1990, i.e. ind", "keywords": ["energy & environment", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS8", "title": "JAPAN – ALCOHOLIC BEVERAGES II", "complainant": "United States, European Communities", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Japanese Liquor Tax Law that established a system of internal taxes applicable to all liquors at dif", "sector": "Other", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel's finding that vodka was taxed in excess of shochu, in violation of Art. III:2, first sentence, accepting the Panel's interpretation that Art. III:2, first sentence requires an examination of the conformity of an internal tax measures by determining two elements: (i) whether the taxed imported and domestic products are like; and (ii) whether the taxes applied to the imported products are in excess of those applied to the like domestic products. • GATT Art. III:2 (nati", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS18", "title": "AUSTRALIA – SALMON", "complainant": "Canada", "respondent": "Australia", "third_parties": [], "agreements": ["SPS Arts. 5.1, 5.5 and 5.6"], "articles": [], "subject": "Australia's import prohibition of certain salmon from Canada.", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 5.1 (risk assessment): The Appellate Body, although reversing the Panel's finding because the Panel had examined the wrong measures (i.e. heat-treatment requirement), still found that the correct measure at issue – Australia's import prohibition – violated Art. 5.1 (and, by implication, Art. 2.2) because it was not based on a “risk assessment” requirement under Art. 5.1. • SPS Art. 5.5 (prohibition on discrimination and disguised restriction on international trade): The Appellate Body upheld the Panel's finding that the import prohibition violated Art. 5.5 (and, by implication Art. ", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS22", "title": "BRAZIL – DESICCATED COCONUT", "complainant": "Philippines", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I, II and VI\nAA Art. 13", "AA Art. 13"], "articles": [], "subject": "A countervailing duty Brazil imposed on 18 August 1995 based on an investigation initiated on 21 Jun", "sector": "Agriculture & Food", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Arts. I (most-favoured-nation treatment), II (schedules of concessions) and VI (anti-dumping and countervailing duties): The Appellate Body upheld the Panel's finding that GATT Arts. I, II and VI did not apply to the Brazilian countervailing duty measure at issue because it was based on an investigation initiated prior to 1 January 1995, the date that the WTO Agreement came into effect for Brazil. Specifically, the Panel found: (i) the subsidy rules in the GATT cannot apply independently of the ASCM; and (ii) non-application of the ASCM renders the subsidy rules in the GATT non-applicab", "keywords": ["agriculture & food", "GATT", "AA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS24", "title": "US – UNDERWEAR", "complainant": "Costa Rica", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6\nGATT Art. X", "GATT Art. X"], "articles": [], "subject": "Quantitative import restriction imposed by the United States, as a transitional safeguard measure un", "sector": "Textiles", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Textiles السعودي — تستحق المتابعة", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6.10 (transitional safeguard measures – prospective application): The Appellate Body reversed the Panel's finding and concluded that in the absence of express authorization, the plain language of Art. 6.10 creates a presumption that a measure may be applied only prospectively, and thus may not be backdated so as to apply as of the date of publication of the importing Member's request for consultation. • ATC Art. 6.2 (transitional safeguard measures – serious damage and causation): The Panel refrained from making a finding on whether the United States demonstrated “serious damage” wi", "keywords": ["textiles", "ATC", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS26", "title": "EC – HORMONES", "complainant": "United States, Canada", "respondent": "European Communities", "third_parties": [], "agreements": ["SPS Arts. 3 and 5"], "articles": [], "subject": "EC prohibition on the placing on the market and the importation of meat and meat products treated wi", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 3.1 (international standards): The Appellate Body rejected the Panel's interpretation and said that the requirement that SPS measures be “based on” international standards, guidelines or recommendations under Art. 3.1 does not mean that SPS measures must “conform to” such standards. • Relationship between SPS Arts. 3.1, 3.2 and 3.3 (harmonization): The Appellate Body rejected the Panel's interpretation that Art. 3.3 is the exception to Arts. 3.1 and 3.2 assimilated together and found that Arts. 3.1, 3.2 and 3.3 apply together, each addressing a separate situation. Accordingly, it re", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS27", "title": "EC – BANANAS III", "complainant": "United States, Mexico, Guatemala, Honduras, Ecuador", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT", "GATS"], "articles": [], "subject": "The European Communities' regime for the importation, distribution and sale of bananas, introduced o", "sector": "Agriculture & Food", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Art. XIII (non-discriminatory administration of quantitative restrictions): The Appellate Body upheld the Panel's finding that the allocation of tariff quota shares to some Members not having a substantial interest in supplying bananas, but not to others, was inconsistent with Art. XIII:1. The Appellate Body also agreed with the Panel that the BFA tariff quota reallocation rules3, under which a portion of a tariff quota share not used by one BFA country could be reallocated exclusively to other BFA countries, were inconsistent with Arts. XIII:1 and XIII:2, chapeau. • Lomé Waiver: The Ap", "keywords": ["agriculture & food", "GATT", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS31", "title": "CANADA – PERIODICALS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. III, XI and XX"], "articles": [], "subject": "(i) Tariff Code 9958, which prohibited the importation into Canada of any periodical that was a “spe", "sector": "Anti-Dumping", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions) and Art. XX(d) (exceptions – necessary to secure compliance with laws): The Panel found that Tariff Code 9958, which prohibited the importation of certain periodicals, violated Art. XI, and was not justified under Art. XX(d) because it could not be regarded as a measure to secure compliance with Canada's Income Tax Act. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Appellate Body reversed the Panel's finding that imported split-run periodicals and domestic non-split run periodicals were “lik", "keywords": ["anti-dumping", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS33", "title": "US – WOOL SHIRTS AND BLOUSES", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ATC Arts. 6 and 2.4"], "articles": [], "subject": "Temporary safeguard measure imposed by the United States in the form of a quota on certain imports f", "sector": "Safeguards", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6 (transitional safeguard measures): The Panel found that the United States violated Arts. 6.2 and 6.3 because it failed to meet the causation and serious damage (and threat of serious damage) requirements therein when imposing its transitional safeguard measure, in particular, by not examining the data relevant to the “woven wool shirts and blouses industry”, as opposed to the “woven shirts and blouses industry in general”. The Panel also considered the list of industry impact factors in Art. 6.3 to be a mandatory list: an investigating authority must demonstrate that it considered", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS34", "title": "TURKEY – TEXTILES", "complainant": "India", "respondent": "Turkey", "third_parties": [], "agreements": ["GATT Arts. XI, XIII and XXIV\nATC Art. 2.", "ATC Art. 2.4"], "articles": [], "subject": "Turkey's quantitative import restrictions pursuant to the Turkey-EC customs union.", "sector": "Textiles", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Arts. XI (prohibition on quantitative restrictions) and XIII (non-discriminatory administration of quantitative restrictions): The Panel found that the quantitative restrictions at issue were inconsistent with Arts. XI and XIII. (Turkey did not deny this.) • ATC Art. 2.4 (prohibition on new restrictions): The Panel found that Turkey's measures were new restrictions, that did not exist at the time of the entry into force of the ATC, and, thus, were prohibited by Art. 2.4. • GATT Art. XXIV (regional trade agreements): The Appellate Body agreed with the Panel's ultimate conclusion that Tur", "keywords": ["textiles", "GATT", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS44", "title": "JAPAN – FILM", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["GATT Arts. XXIII"], "articles": [], "subject": "Actions by Japan affecting the distribution, offering for sale, and internal sale of imported consum", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XXIII:1(b) (non-violation claim): The Panel found that the United States failed to demonstrate that the measures at issue nullified or impaired benefits accruing to the United States within the meaning of Art. XXIII:1(b). The Panel considered that a complaining party must demonstrate three elements under Art. XXIII:1(b): (i) application of a measure by a WTO Member; (ii) a benefit accruing under the relevant agreement: and (iii) nullification or impairment of the benefit as the result of the application of the measure. • GATT Art. III:4 (national treatment – domestic laws and regul", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS46", "title": "BRAZIL – AIRCRAFT", "complainant": "Brazil", "respondent": "Canada", "third_parties": [], "agreements": ["SCM"], "articles": [], "subject": "Brazilian government payment for the regional aircraft export under the interest rate equalization", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 3.1(a) (prohibited subsidies – export subsidies) and Annex I, Illustrative List of Export Subsidies, item (k): Brazil did not dispute that its PROEX interest rate equalization scheme was a subsidy contingent upon export performance, but argued that it was “permitted” under item (k) of the Illustrative List of Export Subsidies. The Appellate Body reversed and modified the Panel's interpretation of “used to secure a material advantage in export credit terms” but upheld the Panel's conclusion that Brazil failed to establish that the payments fell within the first para. of item (k) as ", "keywords": ["subsidies & anti-subsidy", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS50", "title": "INDIA – PATENTS (US)", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Art. 70.8 and 70.9"], "articles": [], "subject": "(i) India's “mailbox rule” – under which patent applications for pharmaceutical and agricultural che", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Appellate Body upheld the Panel's finding that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Appellate Body found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the administrative instructions could be rejected by the court under the contradictory mandator", "keywords": ["agriculture & food", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS54", "title": "INDONESIA – AUTOS", "complainant": "United States, European Communities, Japan", "respondent": "Indonesia", "third_parties": [], "agreements": ["TRIMs Art. 2.1\nGATT Arts. I", "GATT Arts. I"], "articles": [], "subject": "(i) “The 1993 Programme” that provided import duty reductions or exemptions on imports of automotive", "sector": "Automotive", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIMs Agreement Art. 2.1 (local content requirement): 2 The Panel found the 1993 Programme to be in violation of Art. 2.1 because (i) the measure was a “trade-related investment”3 measure; and (ii) the measure, as a local content requirement, fell within para. 1 of the Illustrative List of TRIMs in the Annex to the TRIMs Agreement, which sets out trade-related investment measures that are inconsistent with national treatment obligation under GATT Art. III:4. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Panel found that the sales tax benefits und", "keywords": ["automotive", "TRIMs", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS56", "title": "ARGENTINA – TEXTILES AND APPAREL", "complainant": "United States", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. II and VIII"], "articles": [], "subject": "(i) Argentina's system of minimum specific import duties, known as “DIEM”, on textiles and apparel (", "sector": "Textiles", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II (schedules of concessions): The Appellate Body found Argentina's measure was, in fact, inconsistent with Art. II:1(b). It held that “the application of a type of duty different from the type provided for in a Member's Schedule is inconsistent with GATT Art. II:1(b), first sentence, to the extent that it results in ordinary customs duties being levied in excess of those provided for in that Member's Schedule.” In this case, the Appellate Body concluded that “the structure and design of the Argentine system is such that for any DIEM ... the possibility remains that there is a ‘bre", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS58", "title": "US – SHRIMP", "complainant": "Thailand, Malaysia, Pakistan", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. XI and XX"], "articles": [], "subject": "US import prohibition of shrimp and shrimp products from non-certified countries (i.e. countries tha", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel found that the US prohibition, based on Section 609, on imported shrimp and shrimp products violated Art. XI. The United States apparently conceded the measure's violation of Art. XI because it did not put forward any defending arguments in this regard. • GATT Art. XX(g) (general exceptions – exhaustible natural resources): The Appellate Body held that although the US import ban was related to the conservation of exhaustible natural resources and, thus, covered by an Art. XX(g) exception, it could not be justified under Art. ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS60", "title": "GUATEMALA – CEMENT I", "complainant": "Mexico", "respondent": "Guatemala", "third_parties": [], "agreements": ["DSU Art. 6.2\nADA Art. 17.4", "ADA Art. 17.4"], "articles": [], "subject": "Guatemala's anti-dumping investigation (both the initiation and various decisions and conduct of the", "sector": "Anti-Dumping", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "1998", "summary_ar": "", "summary_en": "• DSU Art. 6.2 and ADA Art. 17.4 (requirements of panel request): The Appellate Body, reversing the Panel, concluded that Mexico had failed to identify in its panel request the “specific measures at issue” in accordance with DSU Art. 6.2 and ADA Art. 17.4, i.e. one of the three measures to be specified in a dispute involving anti-dumping investigations: (i) a definitive antidumping duty, (ii) the acceptance of a price undertaking, or (iii) a provisional anti-dumping measure. According to the Appellate Body, the special dispute settlement rules in the ADA and the DSU provisions together create ", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS62", "title": "EC – COMPUTER EQUIPMENT", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II"], "articles": [], "subject": "The European Communities' application of tariffs on local area networks: (LAN) equipment and multime", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedule of concessions – LAN): The Appellate Body reversed the Panel's finding of a violation by the European Communities of Art. II:1 with respect to LAN equipment on the basis of the Panel's erroneous legal reasoning and consideration of only selective evidence. In this regard the Appellate Body rejected the Panel's finding that a tariff concession in the Schedule can be interpreted in light of an exporting Member's “legitimate expectations” – a concept relevant to a nonviolation complainant under GATT Art. XXIII:1(b) – in the context of a violation complaint. Rather, the ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS69", "title": "EC – POULTRY", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. XIII, X\nLicensing Aga"], "articles": [], "subject": "European Communities' tariff rate quota (TRQ) system incorporated into EC Schedule LXXX with respect", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XIII:2 (non-discriminatory administration of quantitative restrictions): The Appellate Body upheld the Panel's finding that the TRQ must be administered on a non-discriminatory basis – as opposed to it being awarded exclusively to Brazil – based on the text of the EC Schedule LXXX and pursuant to Art. XIII, and thus, the European Communities had acted consistently with its WTO obligations. The Appellate Body also upheld the Panel's finding that, even when a TRQ is the result of an Art. XXVIII compensation negotiation, it must be administered in a non-discriminatory manner (total im", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS70", "title": "CANADA – AIRCRAFT", "complainant": "Brazil", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1 and 4.7"], "articles": [], "subject": "Canadian measures providing various forms of financial support to the domestic civil aircraft indust", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (definition of a subsidy): The Panel found that a “financial contribution” confers a “benefit” and constitutes a subsidy under Art. 1 when provided on terms more advantageous than those otherwise available to the recipient on the market. The Appellate Body, while upholding this finding, concluded that the word “conferred”, in conjunction with “thereby”, calls for an inquiry into what was conferred on the recipient, not an inquiry into the cost to the government as argued by Canada. • ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): The Appellate Body upheld the Panel", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS75", "title": "KOREA – ALCOHOLIC BEVERAGES", "complainant": "United States, European Communities", "respondent": "Korea", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Korea's tax regime for alcoholic beverages, which imposed different tax rates for various categories", "sector": "Other", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's conclusion that the Korean tax measures at issue were inconsistent with Art. III:2, second sentence: More specifically, the Appellate Body upheld the Panel's findings that the products at issue were “directly competitive or substitutable” within the meaning of Art. III:2, second sentence and that Korea's tax measures on alcoholic beverages were applied “so as to afford protection” to domestic production within the meaning of Art. II", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS76", "title": "JAPAN – AGRICULTURAL PRODUCTS II", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7, 5.6 and 5.1"], "articles": [], "subject": "Varietal testing requirement (Japan's Plant Protection Law), under which the import of certain plant", "sector": "Agriculture & Food", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1999", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that Japan's varietal testing requirement was maintained without sufficient scientific evidence in violation of Art. 2.2.3 • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the varietal testing requirement was not justified under Art. 5.7 because Japan did not meet all the requirements for the adoption and maintenance of a provisional SPS measure as set out in Art. 5.7. • SPS Art. 5.6 (appropriate level of protection – alternative measures): Having found that th", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS79", "title": "INDIA – PATENTS (EC)", "complainant": "European Communities", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Arts. 70.8 and 70.9"], "articles": [], "subject": "(i) The insufficiency of the legal regime – India's “mailbox rule” – under which patent applications", "sector": "Intellectual Property", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Panel held that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Panel found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the current administrative instructions could be rejected by the court under the contradictory mandatory provisions of the pertinent In", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS87", "title": "CHILE – ALCOHOLIC BEVERAGES", "complainant": "European Communities", "respondent": "Chile", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Chile's tax measures that imposed an excise tax at different rates – depending on the type of produc", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's finding that Chile's new tax regime for alcoholic beverages violated the national treatment principle under Art. III:2, second sentence. (Chile's appeal was only in regard to the new regime.) The Panel found both Chile's transitional and new tax regimes inconsistent with Art. III:2, second sentence. (“not similarly taxed”): The Appellate Body agreed with the Panel that imported distilled spirits and Chilean pisco, as directly compet", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS90", "title": "INDIA – QUANTITATIVE RESTRICTIONS", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "India's import restrictions that India claimed were maintained to protect its balance-of-payments (B", "sector": "Other", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Art. XI:1 (prohibition on quantitative restrictions): The Panel found, based on the broad scope of a general ban on import restrictions embodied in Art. XI:1, that India's measures, including its discretionary import licensing system, were quantitative restrictions inconsistent with Art. XI:1. • GATT Art. XVIII:11 (BOP measures): The Panel found that as India's monetary reserves were adequate, and, thus, India's BOP measures were not necessary to forestall the threat of, or to stop, a serious decline in its monetary reserves within the meaning of Art. XVIII:9, India had violated Art. XV", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS98", "title": "KOREA – DAIRY", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Definitive safeguard measure.", "sector": "Agriculture & Food", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Agriculture & Food السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): Reversing the Panel's legal reasoning, the Appellate Body held that the clause – “as a result of unforeseen development and of the effect of the obligations incurred by a contracting party under this Agreement, including tariff concessions” – in Art. XIX:1(a), although not an independent condition, describes certain circumstances which must be demonstrated as a matter of fact in order for a safeguard measure to be applied consistently with the requirements of Art. XIX. The Appellate Body concluded that the phrase “as a result of unforeseen develo", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS99", "title": "US – DRAMS", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 11, 2.2, 6.6 and 5.8"], "articles": [], "subject": "United States Department of Commerce (USDOC) regulation (namely, the “three zeroes” rules)2, both as", "sector": "Anti-Dumping", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "1999", "summary_ar": "", "summary_en": "• ADA Art. 11.2 (review of anti-dumping duties – the “likely” standard): The Panel found for Korea and held that the “not likely” standard in the US regulation (as quoted in footnote 2 below), as such, is inconsistent with Art. 11.2 (“likely” standard) because a failure to find that an exporter is “not likely” to dump does not necessarily lead to the conclusion that this exporter is therefore “likely” to dump. The Panel considered that because there are situations where the not “not likely” standard is satisfied but the “likely” standard is not, the “not likely” criterion fails to provide a “d", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS103", "title": "CANADA – DAIRY", "complainant": "Canada, New Zealand", "respondent": "United States", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "Canadian government's support system (Special Milk Classes Scheme) for domestic milk production and", "sector": "Agriculture & Food", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "1999", "summary_ar": "", "summary_en": "• AA Art. 9.1(a) (export subsidies – direct subsidies): Having reversed the Panel's conclusion that Canada's measure involved export subsidies within the meaning of Art 9.1(a) (based on the Panel's erroneous interpretation of the terms “direct subsidies” and “payments-in-kind” under Art. 9.1(a)), the Appellate Body also reversed the Panel's finding that Canada had acted inconsistently with Arts. 3.3 and 8 by providing export subsidies under Art. 9.1(a) – i.e. by exceeding the support reduction commitment levels scheduled by Canada. • AA Art. 9.1(c) (export subsidies – payments financed by virt", "keywords": ["agriculture & food", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS108", "title": "US – FSC", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["SCM"], "articles": [], "subject": "US tax exemptions for Foreign Sales Corporations (FSC)2 in respect of their export-related foreign-s", "sector": "Subsidies & Anti-Subsidy", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a): (1): (ii) (definition of a subsidy – financial contribution): The Appellate Body upheld the Panel's finding that the FSC measure constituted government revenue foregone that was “otherwise due” and, thus a “financial contribution” within the meaning of Art. 1.1. • ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): The Appellate Body upheld the Panel's finding that the FSC measure constituted prohibited export subsidies under Art. 3.1(a) because the FSC exemptions (i) were based upon foreign trade income derived from “export property” and (ii) fell within the langua", "keywords": ["subsidies & anti-subsidy", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS114", "title": "CANADA – PHARMACEUTICAL PATENTS", "complainant": "European Communities", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 27, 28 and 30"], "articles": [], "subject": "Certain provisions under Canada's Patent Act: (i)”regulatory review provision (Sec. 55.2(1))” 2; and", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "Stockpiling provision • TRIPS Arts. 28.1 (patent owner rights) and 30 (exceptions): (Canada practically conceded that the stockpiling provision violated Art. 28.1, which sets out exclusive rights granted to patent owners.) Concerning Canada's defence under Art. 30, the Panel found that the measure was not justified under Art. 30 because there were no limitations on the quantity of production for stockpiling which resulted in a substantial curtailment of extended market exclusivity, and, thus, was not “limited” as required by Art. 30. Accordingly, the Panel concluded that the stockpiling provis", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS121", "title": "ARGENTINA – FOOTWEAR (EC)", "complainant": "Argentina", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Provisional and definitive safeguard measures imposed by Argentina.", "sector": "Safeguards", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): Having determined that any safeguard measure imposed after the entry into force of the WTO Agreement must comply with the provisions of both the SA and GATT Art. XIX, the Appellate Body reversed the Panel's conclusion that the GATT Art. XIX:1(a) “unforeseen developments” clause does not add anything additional to the SA in respect of the conditions under which a safeguard measure may be applied. It found instead that Art. XIX:1(a), although an independent obligation, describes certain circumstances that must be demonstrated as a matter of fact. T", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS122", "title": "THAILAND – H-BEAMS", "complainant": "Poland", "respondent": "Thailand", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 17.6"], "articles": [], "subject": "Thailand's definitive anti-dumping determination.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 5 (initiation of investigation): The Panel rejected Poland's claim that the Thai authorities' initiation of the investigation could not be justified due to the insufficiency of evidence originally contained in the application. The Panel considered that the application need not contain analysis, but only information. The Panel also rejected Poland's claim that Thailand violated Art. 5.5 by failing to provide a written notification of the filing of application for initiation of investigation. The Panel considered that a formal meeting could satisfy the requirement. • ADA Art. 2.2 (dum", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS126", "title": "AUSTRALIA – AUTOMOTIVE LEATHER II", "complainant": "United States", "respondent": "Australia", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1"], "articles": [], "subject": "Australian government's assistance (“grant contract” ($A 30 million) and “loan contract” ($A 25 mill", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): As for the grant contract, the Panel found that the payments under the grant contract were subsidies prohibited under Art. 3.1(a), on the ground that the payments concerned were in fact “tied to” export performance. In respect of the loan contract, the Panel concluded that the payments under the loan contract did not violate Art. 3.1(a) because there was nothing in the terms of the loan contract itself that suggested a “specific link” to actual or anticipated exportation or export earnings. • ASCM Art. 4.7 (recommendation to withdra", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS132", "title": "MEXICO – CORN SYRUP", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["ADA Arts. 3, 5, 6, 7, 10 and 12"], "articles": [], "subject": "Mexico's definitive anti-dumping duty measure.", "sector": "Anti-Dumping", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• ADA Art. 5.2 (initiation of investigation – application): The Panel rejected the US claim that the anti-dumping application in this case was inconsistent with Art. 5.2 due to insufficient evidence of threat of material injury. The applicant need provide only such information as is reasonably available to it. • ADA Art. 12.1 (notice of initiation): The Panel rejected the US claim that Art. 12.1 requires the investing authority to address, in the notice of initiation, the definition of the relevant domestic industry. • ADA Arts. 5.3 (initiation of investigation), 5.8 (termination of investigat", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS135", "title": "EC – ASBESTOS", "complainant": "European Communities", "respondent": "Canada", "third_parties": [], "agreements": ["GATT", "TBT"], "articles": [], "subject": "France's ban on asbestos (Decree No. 96-1133).", "sector": "Standards & TBT", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2001", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (technical regulation): The Appellate Body, having rejected the Panel's approach of separating the measure into the ban and the exceptions, reversed the Panel and concluded that the ban as an “integrated whole” was a “technical regulation” as defined in Annex 1.1 and thus covered by the TBT Agreement, as (i) the products subject to the ban were identifiable (i.e. any products containing asbestos); (ii) the measure was a whole laid down product characteristics; and (iii) compliance with the measure was mandatory. However, the Appellate Body did not complete the legal analysis of", "keywords": ["standards & tbt", "GATT", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS136", "title": "US – 1916 ACT", "complainant": "European Communities, Japan", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI\nADA Arts. 1, 4, 5 and 18", "ADA Arts. 1, 4, 5 and 18"], "articles": [], "subject": "United States' Anti-Dumping Act of 1916, which provided for, inter alia, a private right of action, ", "sector": "Anti-Dumping", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. VI and ADA (applicability): The Appellate Body upheld the Panel's finding that GATT Art. VI and the ADA applied to the 1916 Act. Art. VI applies to action taken in response to situations involving dumping and the 1916 Act provided for specific action to be taken in situations that present the constituent elements of dumping within the meaning of that provision. • GATT Art. VI and ADA (substantive violations): 2 The Appellate Body upheld the Panel's findings on the following claims: the 1916 Act was inconsistent with: (i) GATT Art. VI (anti-dumping duties) which, read in conjunction", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS138", "title": "US – LEAD AND BISMUTH II", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "United States Department of Commerce's (USDOC) reliance on “change-in-ownership methodology” in", "sector": "Subsidies & Anti-Subsidy", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• ASCM Arts. 1.1(b) (definition of a subsidy – benefit), 10 (application of GATT Art. VI) and 21.2 (review of countervailing duties): The Appellate Body upheld the Panel's finding that the USDOC should not have presumed that the non-recurring subsidy given to a state-owned enterprise (BSC in this case) would have “passed through” to subsequent companies (UES and BSplc/GKN) when that state-owned enterprise (BSC) had been privatized. Rather, the USDOC was required under Art. 21.2 to examine, in the reviews at issue, whether a “benefit” had been conferred on the new owners of the company (UES and", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS139", "title": "CANADA – AUTOS", "complainant": "European Communities, Japan", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3 and 4.7\nGATS Arts. I and", "GATS Arts. I and II"], "articles": [], "subject": "Canada's import duty exemption for imports by certain manufacturers, in conjunction with the Canadia", "sector": "Services", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. I (most-favoured-nation treatment): The Appellate Body upheld the Panel's finding that the duty exemption was inconsistent with the most-favoured-nation treatment obligation under Art. I:1 on the ground that Art. I:1 covers not only de jure but also de facto discrimination and that the duty exemption at issue in reality was given only to the imports from a small number of countries in which an exporter was affiliated with eligible Canadian manufacturers/importers. The Panel rejected Canada's defence that Art. XXIV allows the duty exemption for NAFTA members (Mexico and the United S", "keywords": ["services", "ASCM", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS141", "title": "EC – BED LINEN", "complainant": "European Communities", "respondent": "India", "third_parties": [], "agreements": ["ADA"], "articles": [], "subject": "Definitive anti-dumping duties imposed by the European Communities, including the European", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Appellate Body upheld the Panel's finding that the practice of “zeroing”, as applied by the European Communities in this case in establishing “the existence of margins of dumping”, was inconsistent with Art. 2.4.2. By “zeroing” the “negative dumping margins”, the European Communities had failed to take fully into account the entirety of the prices of some export transactions. As a result, the European Communities did not establish “the existence of margins of dumping” for cotton-type bed linen on the basis of a comparison of the weighted ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS146", "title": "INDIA – AUTOS", "complainant": "United States, European Communities", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. III, XI and XVIII", "DSU Art. 19.1"], "articles": [], "subject": "India's (i) indigenization (local content) requirement; and (ii) trade balancing requirement (export", "sector": "Automotive", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2002", "summary_ar": "", "summary_en": "Indigenization requirement • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel concluded that the measure violated Art. III:4, as the indigenization requirement modified the conditions of competition in the Indian market “to the detriment of imported car parts and components”. Trade balancing requirement • GATT Art. XI:1 (prohibition on quantitative restrictions): Having found that “any form of limitation imposed on, or in relation to importation constitutes a restriction on importation within the meaning of Art. XI”, the Panel found that India's trade balancing r", "keywords": ["automotive", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS152", "title": "US – SECTION 301 TRADE ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Art. 23.2"], "articles": [], "subject": "US legislation (i.e. Sections 301-310 of the Trade Act of 1974) authorizing certain actions by the O", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• DSU Art. 23.2(a) (prohibition on unilateral determinations – Section 304): Based on the terms of Art. 23.2(a), the Panel first set out that it is for the WTO, through the DSU process, and not an individual WTO Member, to determine that a measure is inconsistent with WTO obligations. The Panel then concluded that Section 304 was “not inconsistent” with US obligations under Art. 23.2(a) because, while the statutory language of Section 304 in itself constituted a serious threat that unilateral determinations contrary to Art. 23.2(a) might be taken, the United States had (i) lawfully removed thi", "keywords": ["other", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS155", "title": "ARGENTINA – HIDES AND LEATHER", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. III"], "articles": [], "subject": "(i) Argentine regulations by which representatives of the Argentine leather tanning industry were pr", "sector": "Other", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2001", "summary_ar": "", "summary_en": "Regulations on export control • GATT Art. XI:1 (prohibition on quantitative restrictions): The Panel rejected the EC claim that the Argentine regulations on export procedures were an export restriction prohibited by Art. XI. The European Communities had failed to meet its burden of proving that the presence of the tanners' representatives during customs procedures, along with the disclosure of information about the slaughterhouses and any possible abuse of this information, was an export restriction under Art. XI:1. • GATT Art. X:3(a) (trade regulations – uniform, impartial and reasonable admi", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS156", "title": "GUATEMALA – CEMENT II", "complainant": "Guatemala", "respondent": "Mexico", "third_parties": [], "agreements": ["ADA"], "articles": [], "subject": "Guatemala's anti-dumping investigation on certain imports.", "sector": "Anti-Dumping", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2000", "summary_ar": "", "summary_en": "• ADA Art. 5.3 (initiation of investigation – application) and 5.8 (initiation of investigation – insufficient evidence): The Panel found that Guatemala violated Art. 5.3 because the application for the initiation of anti-dumping investigation did not have sufficient evidence of dumping, threat of injury and causal link to justify the initiation of the investigation. The Panel noted that the evidentiary standards of Art. 2 (dumping) and of Art. 3.7 (threat of injury) are relevant to an investigating authorities' consideration under Art. 5.3. Given that it had already found that there was insuf", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS160", "title": "US – SECTION 110(5) COPYRIGHT ACT", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["TRIPS Arts. 9 and 13\nBerne Convention an"], "articles": [], "subject": "Section 110 of the US Copyright Act that provides for limitations on exclusive rights granted to cop", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• “Minor exceptions” doctrine: Regarding the US argument that limitations on exclusive rights in the US Copyright Act are justified under TRIPS Art. 13, as Art 13 “clarifies and articulates the 'minor exceptions' doctrine”, the Panel concluded as an initial matter: (i) that there is a “minor exceptions” doctrine that applies to Berne Convention Art. 11bis and 113; and (ii) that the doctrine has been incorporated into the TRIPS Agreement. • TRIPS Art. 13 (limitations on exclusive copyrights): The Panel clarified three criteria that parties have to cumulatively meet to make limitations or except", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS161", "title": "KOREA – VARIOUS MEASURES ON BEEF", "complainant": "United States, Korea", "respondent": "Australia", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "(i) Korea's measures affecting the importation, distribution and sale of beef, (ii) Korea's “dual re", "sector": "Agriculture & Food", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2001", "summary_ar": "", "summary_en": "• AA Art. 3.2 (domestic support): While upholding the Panel's conclusion that Korea miscalculated its domestic support (AMS) for beef, the Appellate Body reversed the Panel's ultimate finding that Korea acted inconsistently with Art. 3.2 by exceeding its commitment levels for total support for 1997 and 1998 as the Panel had also relied on an improper methodology for its own calculations. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Appellate Body agreed with the Panel's ultimate conclusion that Korea's dual retail system (requiring imported beef to be sold in sep", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS163", "title": "KOREA – PROCUREMENT", "complainant": "United States", "respondent": "Korea", "third_parties": [], "agreements": ["GPA Arts. I and XXII"], "articles": [], "subject": "Other", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• GPA Art. I (scope of Korea's GPA Appendix I commitment): The Panel found, based on the terms of Korea's concessions in its GPA Schedule and the supplementary negotiating history of the Schedule, that the entities allegedly responsible for IIA procurement – i.e. NADG or KAA – were not entities covered by Korea's GPA schedule, and thus concluded that the IIA project was not covered by Korea's commitments under the GPA. • GPA Art. XXII:2 (non-violation nullification or impairment): Regarding the US non-violation claim under GPA Art. XXII:2, which was based on the frustration of reasonably expec", "keywords": ["other", "GPA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS165", "title": "US – CERTAIN EC PRODUCTS", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Increased bonding requirements imposed on 3 March 1999 before the issuance of the Art. 22.6 Arbitrat", "sector": "Other", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2001", "summary_ar": "", "summary_en": "• GATT Art. I (most-favoured-nation treatment): The Panel found that the bonding requirements violated the most-favourednation principle of Art. I as it only applied to imports from the European Communities. • GATT Art. II (schedules of concessions): The Appellate Body reversed the Panel majority's finding that the bonding requirements violated Art. II:1(a) and II:1(b), first sentence, because the Panel's finding was related to the later measure (100 per cent tariff duties) that the United States had imposed subsequent to the Art. 22.6 Arbitration's decision, which was outside the Panel's term", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS166", "title": "US – WHEAT GLUTEN", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Definitive safeguard measure imposed by the United States.", "sector": "Agriculture & Food", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Agriculture & Food السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• SA Art. 2 (conditions for safeguard measures – increased imports): The Panel found that the United States International Trade Commission's (ITC) finding of increased imports was consistent with SA Art. 2.1 and GATT Art. XIX, as the imports data indicated a “sharp and substantial rise” through the end of the review period. • SA Art. 4.2(a) (injury determination – injury factors): Reversing the Panel's legal interpretation, the Appellate Body held that investigating authorities must examine not only all the factors listed in Art. 4.2(a), but also “all other relevant factors”, including those f", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS170", "title": "CANADA – PATENT TERM", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 33 and 70"], "articles": [], "subject": "Canada's Patent Act, Section 45, which provided the length of the patent protection for patents file", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2000", "summary_ar": "", "summary_en": "• TRIPS Art. 70.1 and 70.2 (protection of existing subject matter): (Art. 70.2) Having found that “a treaty applies to existing rights, even when those rights result from 'acts which occurred' before the treaty entered into force” and Art. 70.2 applies to existing inventions (rights) under Old Act patents whose patents were granted (acts) before the date of entry into force of the TRIPS Agreement, the Appellate Body concluded that Canada was bound by the obligation to provide existing patented inventions with a patent term of not less than 20 years from the filing date as required under Art. 3", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS174", "title": "EC – TRADEMARKS AND GEOGRAPHICAL INDICATIONS", "complainant": "United States, Australia", "respondent": "European Communities", "third_parties": [], "agreements": ["TRIPS Arts. 3, 4, 16, 17 and 24\nGATT Art", "GATT Arts. III"], "articles": [], "subject": "EC Regulation related to the protection of geographical indications and designations of origin (GIs)", "sector": "Intellectual Property", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "National treatment (TRIPS Art. 3.1 and GATT Art. III:4) • Availability of protection: The Panel found that the equivalence and reciprocity conditions in respect of GI protection under the EC Regulation3 violated the national treatment obligations under TRIPS Art. 3.1 and GATT Art. III:4 by according less favourable treatment to non-EC nationals and products, than to EC nationals and products. By providing, “formally identical”, but in fact different procedures based on the location of a GI, the European Communities in fact modified the “effective equality of opportunities” between different na", "keywords": ["intellectual property", "TRIPS", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS176", "title": "US – SECTION 211 APPROPRIATIONS ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["TRIPS Arts. 2, 3, 4, 15, 16 and 42\nParis"], "articles": [], "subject": "Section 211 of the US Omnibus Appropriations Act of 1998, prohibiting those having an interest in", "sector": "Intellectual Property", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2002", "summary_ar": "", "summary_en": "Section 211(a)(1) • TRIPS Art. 15 (trademarks – protectable subject matter) and Art. 2.1 (Paris Convention Art. 6quinquies A(1): As Art. 15.1 embodies a definition of a trademark and sets forth only the eligibility criteria for registration as trademarks (but not an obligation to register “all” eligible trademarks), the Appellate Body found that Section 211(a)(1) was not inconsistent with Art. 15.1, as the regulation concerned “ownership” of a trademark. The Appellate Body also agreed with the Panel that Section 211(a)(1) was not inconsistent with Paris Convention Art. 6quinquies A(1), which a", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS177", "title": "US – LAMB", "complainant": "United States, New Zealand", "respondent": "Australia", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "A definitive safeguard measure imposed by the United States.", "sector": "Safeguards", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): The Appellate Body held that an investigating authority must demonstrate the existence of unforeseen developments “in the same report of the competent authorities” as that containing other findings related to the safeguard investigation at issue to show a “logical connection” between the conditions set forth in Art. XIX and the “circumstances” such as “unforeseen developments”. As there was no such demonstration in the United States International Trade Commission (ITC) Report, the Panel's ultimate finding that the United States violated Art. XIX:", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS179", "title": "US – STAINLESS STEEL", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2"], "articles": [], "subject": "Definitive anti-dumping duties imposed by the United States on certain steel imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 2.4.1 (dumping determination – currency conversion): Having found that where the prices being compared (i.e. export price and normal price) were already in the same currency, “currency conversion” was not required and thus not permissible under Art. 2.4.1, the Panel concluded that the United States acted inconsistently with Art. 2.4.1 by making a currency conversion that was not required in the Sheet investigation, but did not act inconsistently with Art. 2.4.1 in the Plate investigation. • ADA Art. 2.4 (dumping determination – unpaid sales): In calculating a “constructed export pri", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS184", "title": "US – HOT-ROLLED STEEL", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6 and 9"], "articles": [], "subject": "US definitive anti-dumping duties on certain imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 (evidence – facts available): The Appellate Body upheld the Panel's findings that the United States acted inconsistently with Art. 6.8 in applying facts available to exporters, as the United States Department of Commerce (USDOC) had rejected certain information submitted after the deadline without considering whether it was still submitted within a reasonable period of time. The Appellate Body upheld the Panel's finding that the United States acted inconsistently with Art. 6.8 and Annex II when it applied “adverse” facts available to an exporter in respect of certain resale pric", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS189", "title": "ARGENTINA – CERAMIC TILES", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2 and 6"], "articles": [], "subject": "Argentina's definitive anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 and Annex II (evidence – facts available): The Panel found that Art. 6.8, in conjunction with Annex II(6), requires an investigating authority to inform the party supplying information on the reasons why evidence or information is not accepted, to provide an opportunity to provide further explanation within a reasonable period, and to give, in any published determinations, the reasons for the rejection of evidence of information. The Panel then concluded that the Argentine investigating authority (DCD) acted inconsistently with these requirements under Art. 6.8 by failing to exp", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS192", "title": "US – COTTON YARN", "complainant": "Pakistan", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6"], "articles": [], "subject": "Transitional safeguard remedy imposed by the United States under the ATC on certain imports.", "sector": "Safeguards", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ATC Art. 6.2 (transitional safeguard measure – scope of domestic industry): The Appellate Body upheld the Panel's ultimate conclusion that the United States acted inconsistently with Art. 6.2 by excluding from the scope of the domestic industry captive production of yarn (i.e. yarn produced by and processed and consumed within integrated producers for their own use and processing), which was found to be “directly competitive” with yarn offered for sale on the merchant (open) market. In this regard, the Appellate Body considered the term “directly competitive” to suggest a focus on the compet", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS194", "title": "US – EXPORT RESTRAINTS", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 1.1"], "articles": [], "subject": "Treatment of “export restraints” 2 under US countervailing duty (CVD) law (statute), in light of the", "sector": "Subsidies & Anti-Subsidy", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2001", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (a): (1): (iv) (definition of a subsidy – financial contribution): The Panel first concluded that an “export restraint” cannot constitute government-entrusted or government-directed provision of goods in the sense of subpara. (iv) of Art. 1.1(a)(1), and thus does not constitute a “financial contribution” within the meaning of Art. 1.1. According to the Panel, the “entrusts or directs” standard of subpara. (iv) requires an “explicit and affirmative action of delegation or command”, rather definition of a subsidy – than mere government intervention in the market by itself which l", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS202", "title": "US – LINE PIPE", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["SA Arts. 2, 3, 4, 5 and 9"], "articles": [], "subject": "US safeguard measure on certain imports.", "sector": "Safeguards", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• SA Arts. 3.1 and 4.2(c) (safeguard investigation – injury determination): The Appellate Body reversed the Panel's finding that the United States violated Arts. 3.1 and 4.2(c) by failing to publish in its investigation report a discrete finding or reasoned conclusion that the increased imports caused either “serious injury” or “threat of serious injury”, on the ground that the phrase “cause or threaten to cause” should be read to mean that an investigating authority has to conclude either one or both in combination as the US authority had done in the case at hand. • SA Arts. 2 and 4 (parallel", "keywords": ["safeguards", "SA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS204", "title": "MEXICO – TELECOMS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATS Art I"], "articles": [], "subject": "Mexico's domestic laws and regulations that govern the supply of telecommunication services and fede", "sector": "Services", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2004", "summary_ar": "", "summary_en": "• GATS Art. I:2(a) (cross border supply): The Panel found that the services at issue whereby US suppliers link their networks at the border with those of Mexican suppliers for termination within Mexico are services supplied cross-border within the meaning of Art. I:2(a), as the provision is silent as regards the place where the supplier operates, or is present, and thus is not directly relevant to the definition of “cross-border supply”. • Mexico's Reference Paper3 , Sections 2.1 and 2.2: The Panel found that (i) Mexico's commitments under Section 2 of Mexico's Reference Paper applied to the i", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS206", "title": "US – STEEL PLATE", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 6.8, 15 and 18.4"], "articles": [], "subject": "US imposition of anti-dumping duties on certain imports manufactured by Steel Authority of India, Lt", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 18.4 (conformity with the ADA): The Panel held that the US authority's practice in the application of “facts available” was not a measure that could be the subject of a claim. First, because such practice could be changed by the authority as long as it provided a reason for the change. Moreover, according to past WTO jurisprudence, a law can only be found inconsistent with WTO obligations if it mandates a violation. Second, the “practice” challenged by India was not within the scope of Art. 18.4, which only refers to “laws, regulations and administrative procedures”. • ADA Art. 6.8 ", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS207", "title": "CHILE – PRICE BAND SYSTEM", "complainant": "Chile", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Chile's Price Band System, governed by Rules on the Importation of Goods, through which the tariff r", "sector": "Agriculture & Food", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2002", "summary_ar": "", "summary_en": "• DSU Art. 11 (standard of review): The Appellate Body reversed the Panels findings under GATT Art. II:1(b), second sentence, on the grounds that it was a claim that had not been raised by Argentina in its panel request or any subsequent submissions, and the Panel, by assessing a provision that was not part of the matter before it, acted ultra petita and in violation of DSU Art. 11. The Appellate Body also stated that consideration by a panel of claims not raised by the complainant deprived Chile of its due process rights under the DSU. • AA Art. 4.2, footnote 1 (market access): The Appellate ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS211", "title": "EGYPT – STEEL REBAR", "complainant": "Turkey", "respondent": "Egypt", "third_parties": [], "agreements": ["ADA Arts. 2, 3 and 6"], "articles": [], "subject": "Egypt's definitive anti-dumping measures.", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 3.4 (injury determination – injury factors): The Panel interpreted evaluation under Art. 3.4 to mean a process of analysis and interpretation of the facts established, in relation to each listed factor. In the light of this interpretation, the Panel concluded that Egypt acted inconsistently with Art. 3.4 in failing to evaluate six of the factors (productivity, actual and potential negative effects on cash flow, employment, wages and ability to raise capital or investments) as claimed by Turkey but was not in violation with regard to two of the factors (capacity utilization, return o", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS212", "title": "US – COUNTERVAILING MEASURES ON CERTAIN EC PRODUCTS", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1, 14 and 21"], "articles": [], "subject": "US countervailing duty law governing the treatment of subsidies provided to state-owned companies", "sector": "Subsidies & Anti-Subsidy", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2003", "summary_ar": "", "summary_en": "• ASCM Arts. 1 (definition of a subsidy) and 14 (benefit – calculation of amount of subsidy): The Appellate Body reversed the Panel in its findings and stated instead that privatizations at arm's length and at fair market value gave rise to a rebuttable presumption that a benefit ceased to exist after such privatization. It shifts the burden on the investigation authority to establish that the benefits from the previous financial contribution does indeed continue beyond such privatization. • ASCM Art. 19.1 (original investigation), Art. 21.2 (administrative review) and Art. 21.3 (sunset review", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS213", "title": "US – CARBON STEEL", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 21.3"], "articles": [], "subject": "US laws, regulations, administrative procedures and policy bulletin governing “sunset” reviews of", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 21.3 (sunset review – de minimis standard): The Appellate Body reversed the Panel's finding that the US law was in violation of Art 21.3, on the grounds that Art. 21.3 does not require the application of a 1 per cent de minimis standard in sunset reviews. The Appellate Body disagreed with the Panel's reasoning that the de minimis requirement of Art. 11.9 of the ASCM (which applies to original investigations) is implied in Art. 21.3, on the grounds that Art. 21.3 does not have an express reference to the de minimis standard nor is there a textual link (cross-reference) between the t", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS217", "title": "US – OFFSET ACT (BYRD AMENDMENT)", "complainant": "European Communities, Japan, Canada, India, Australia, Mexico, Korea, Chile, Thailand, Indonesia", "respondent": "Brazil", "third_parties": [], "agreements": ["SCM", "ADA"], "articles": [], "subject": "US Continued Dumping and Subsidy Act of 2000 under which anti-dumping and countervailing duties", "sector": "Subsidies & Anti-Subsidy", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Art. 18.1 (specific action against dumping) and ASCM Art. 32.1 (specific action against subsidies): The Appellate Body upheld the Panel's analysis that the US measure was a specific action against dumping of exports and of subsidies as it was related to the determination of, and designed and structured to dissuade the practice of, dumping or subsidization. On this basis the Appellate Body held that the US measure was inconsistent with the ADA and the ASCM as it was a specific action that was not permissible under the said agreements. • ADA Art. 5.4 (initiation of dumping investigation – ", "keywords": ["subsidies & anti-subsidy", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS219", "title": "EC – TUBE OR PIPE FITTINGS", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["ADA Arts. 1, 2 and 3\nGATT Art. VI", "GATT Art. VI"], "articles": [], "subject": "EC Regulation imposing anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. VI:2 (imposition and collection of anti-dumping duties) and ADA Art. 1 (principles): The Appellate Body agreed with the Panel that there was nothing in the ADA that requires investigating authorities to reassess a determination of dumping on the basis of a devaluation occurring during the period of investigation (POI), and thus upheld the Panel's rejection of Brazil's claims. • ADA Art. 2.2.2, chapeau (dumping determination – normal value): The Panel rejected Brazil's claim that the EC authorities should have excluded low volume sales figures from their calculation of “normal value", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS221", "title": "US – SECTION 129(C)(1) URAA", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["GATT\nADA\nASCM", "ADA\nASCM", "ASCM"], "articles": [], "subject": "Section 129(c)(1) of the Uruguay Round Agreements Act of the United States, which established, inter", "sector": "Subsidies & Anti-Subsidy", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• The Panel rejected Canada's claim that Section 129(c)(1) mandated action that was inconsistent with the GATT, the ADA and the ASCM, as the Panel found that Canada had failed to establish its claim. Canada claimed that Section 129(c)(1) had the effect of precluding the United States from implementing adverse WTO reports with respect to what it termed “prior unliquidated entries”2 (i.e. entries made before the end of the reasonable period of time for implementing adverse WTO reports that were not liquidated as of that date). The Panel found, however, that Section 129(c)(1) applied only to the ", "keywords": ["subsidies & anti-subsidy", "GATT", "ADA", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS222", "title": "CANADA – AIRCRAFT CREDITS AND GUARANTEES", "complainant": "Brazil", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1 and 3.1"], "articles": [], "subject": "Financing, loan guarantees or interest rate support provided by the Canadian Export Development", "sector": "Subsidies & Anti-Subsidy", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Arts. 1 (definition of a subsidy) and 3.1(a) (prohibited subsidies – as such challenge): The Panel found that the EDC and IQ programmes as such were not inconsistent with Art. 3.1(a) as Brazil had failed to demonstrate any specific provision in the relevant legal instruments that suggested that the EDC and IQ programmes (and related measures) mandated the conferral of a benefit, and thereby subsidization, within the meaning of Art. 1. The Panel found that even if EDC had the “ability”, and the IQ “could” confer such a benefit, this did not necessarily mean that these programmes were req", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS231", "title": "EC – SARDINES", "complainant": "Peru", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Annex 1.1 and Art. 2.4"], "articles": [], "subject": "EC Regulation establishing common marketing standards for preserved sardines, including a specificat", "sector": "Standards & TBT", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2002", "summary_ar": "", "summary_en": "• TBT Agreement Annex 1.1 (technical regulation): The Appellate Body upheld the Panel's finding that the EC Regulation was a “technical regulation” within the meaning of Annex 1.1 as it fulfilled the three criteria laid down in the Appellate Body report in EC – Asbestos: (i) the document applied to an identifiable product or group of products; (ii) it lays down one or more product characteristics; and (iii) compliance with the product characteristics was mandatory. • TBT Agreement Art. 2.4 (international standard): The Appellate Body upheld the Panel's finding that the definition of “standard”", "keywords": ["standards & tbt", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS236", "title": "US – SOFTWOOD LUMBER III", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 14, 17 and 20"], "articles": [], "subject": "Preliminary countervailing duty determination and preliminary critical circumstances determination m", "sector": "Subsidies & Anti-Subsidy", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a): (1): (iii) (definition of a subsidy – financial contribution): The Panel concluded that the US authorities' determination that the Canadian provincial stumpage programme constituted a “financial contribution” by the government within the terms of Art. 1.1(a)(iii) was not inconsistent with the ASCM. The Panel considered that the Canadian government act of allowing companies to cut the trees amounted to the “supply” of standing timber, which is a good within the meaning of Art. 1.1(a)(1)(iii). • ASCM Art. 14 and 14(d) (benefit – calculation of amount of subsidy): The Panel co", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS238", "title": "ARGENTINA – PRESERVED PEACHES", "complainant": "Chile", "respondent": "Argentina", "third_parties": [], "agreements": ["SA Arts. 2.1, 4.1 and 4.2\nGATT Art. XIX", "GATT Art. XIX"], "articles": [], "subject": "Argentina's safeguard measures imposed, in the form of specific duties, on preserved peaches from al", "sector": "Safeguards", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): The Panel noted the two distinct requirements under Art. XIX:1(a) to be fulfilled before the imposition of safeguard measures: (i) demonstration of increased imports and (ii) demonstration of unforeseen developments. The Panel concluded that on the facts of the case it was not evident that the Argentine authorities had discussed or offered any explanation on why the developments were “unforeseen” at the time of the negotiation of the obligations, and, therefore, that they had not fulfilled the criteria of Art. XIX:1(a). • SA Arts. 2.1 and 4.2(a) ", "keywords": ["safeguards", "SA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS241", "title": "ARGENTINA – POULTRY ANTI-DUMPING DUTIES", "complainant": "Brazil", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 6"], "articles": [], "subject": "Definitive anti-dumping measures, in the form of specific anti-dumping duties, imposed by Argentina ", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Art. 5.3 (initiation of investigation – application): The Panel found that, by basing the determination of initiation of an investigation on “some” instances of dumping, Argentina violated Art. 5.3 as a dumping determination should be made in respect of the product as a whole for “all” comparable transactions, not for individual transactions. • ADA Art. 5.8 (initiation of investigation – insufficient evidence): The Panel found that Argentina violated Art. 5.8 as it failed to reject an application for investigation which was based on insufficient evidence following the issuance of a negat", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS243", "title": "US – TEXTILES RULES OF ORIGIN", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ROA Art. 2"], "articles": [], "subject": "Rules of origin applied by the United States to textiles and apparel products and used in administer", "sector": "Textiles", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2003", "summary_ar": "", "summary_en": "• ROA Art. 2(b) (trade objectives): The Panel rejected India's claim and concluded that although the objectives of protecting the domestic industry against import competition and of favouring imports from one Member over imports from another may in principle be considered to constitute “trade objectives” for which rules of origin may not be used, India had failed to establish that US rules of origin were being administered to pursue trade objectives in violation of Art. 2(b). • ROA Art. 2(c), first sentence (restrictive, distorting or disruptive effects): The Panel rejected India's claim on th", "keywords": ["textiles", "ROA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS244", "title": "US – CORROSION RESISTANT STEEL SUNSET REVIEW", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 11.3"], "articles": [], "subject": "(i) US statute for sunset review of anti-dumping duties, in conjunction with the Statement of Admini", "sector": "Metals & Mining", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review • ADA Art. 11.3 (continuation of dumping and injury): The Appellate Body made some general observations with regard to such a determination: (i) the second condition of Art. 11.3 involved a prospective determination on the part of the investigating authorities, requiring a forward-looking analysis of what would be likely to occur if the duty were terminated; (ii) as to the standard of “likely”, a positive determination may be made only if the evidence demonstrated that dumping would be “probable” (not possible or plausible) if the duty were terminated; and (iii) Art. 11.3 does no", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS245", "title": "JAPAN – APPLES", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7 and 5.1\nDSU Art. 11", "DSU Art. 11"], "articles": [], "subject": "Certain Japanese measures restricting imports of apples on the basis of concerns about the risk of", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2003", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that the measure was maintained “without sufficient scientific evidence” inconsistently with Art. 2.2, as there was a clear disproportion (and thus no rational or objective relationship) between Japan's measure and the “negligible risk” identified on the basis of the scientific evidence. • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the measure was not a provisional measure justified within the meaning of Art. 5.7, as the measure was not imposed in respect o", "keywords": ["agriculture & food", "SPS", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS246", "title": "EC – TARIFF PREFERENCES", "complainant": "European Communities", "respondent": "India", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "European Communities' generalized tariff preferences (GSP) scheme for developing countries and", "sector": "Other", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2004", "summary_ar": "", "summary_en": "• GATT Art. I:1 (most-favoured-nation treatment): The Panel found that the tariff advantages under the Drug Arrangements were inconsistent with Art. I:1, as the tariff advantages were accorded only to the products originating in the 12 beneficiary countries, and not to the like products originating in all other Members, including those originating in India. • Enabling Clause, para. 2(a): The Appellate Body agreed with the Panel that the Enabling Clause is an “exception” to GATT Art. I:1, and concluded that the Drug Arrangements were not justified under para. 2(a) of the Enabling Clause, as the", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS248", "title": "US – STEEL SAFEGUARDS", "complainant": "Japan, Brazil, Korea, Norway, Switzerland, New Zealand", "respondent": "China", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "US definitive safeguard measures on a wide range of steel products.", "sector": "Metals & Mining", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): The Appellate Body upheld the Panel's findings (i) that an investigating authority must provide a “reasoned conclusion” in relation to “unforeseen developments” for each specific safeguard measure at issue; and (ii) that the United States International Trade Commission (ITC) relevant explanation was not sufficiently reasoned and adequate and thus inconsistent with GATT Art. XIX:1(a). • SA Arts. 2.1 and 3.1 (conditions for safeguard measures – increased imports): Recalling the relevant legal standard that it elaborated in Argentina – Footwear Safe", "keywords": ["metals & mining", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS257", "title": "US – SOFTWOOD LUMBER IV", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1", "GATT Art. VI"], "articles": [], "subject": "US final countervailing duty determination.", "sector": "Subsidies & Anti-Subsidy", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2004", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a): (1): (iii) (definition of a subsidy – financial contribution): The Appellate Body upheld the Panel's finding that the United States Department of Commerce's (USDOC) “[d]etermination that the Canadian provinces were providing a financial contribution in the form of the provision of a good by providing standing timber to timber harvesters through the stumpage programmes” was not inconsistent with Art. 1.1(a)(1)(iii). It found that the ordinary meaning of “goods” should not be read so as to exclude tangible items of property, like trees, that are severable from land and also, ", "keywords": ["subsidies & anti-subsidy", "ASCM", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS264", "title": "US – SOFTWOOD LUMBER V", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 4, 5, 6, 9 and 18"], "articles": [], "subject": "US final anti-dumping duties.", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2004", "summary_ar": "", "summary_en": "Dumping determination • ADA Art. 2.4 and 2.4.2 (zeroing): The Appellate Body upheld the Panel's (majority) finding that the US acted inconsistently with the first sentence of Art. 2.4.2 in determining dumping margins on the basis of a methodology incorporating zeroing in the aggregation of results of comparisons of weighted average normal value with a weighted average of prices of all comparable export transactions. The Appellate Body ruled in this case only on the first methodology provided for in Art. 2.4.2, first sentence, that is weighted average normal value compared with a weighted avera", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS265", "title": "EC – EXPORT SUBSIDIES ON SUGAR", "complainant": "Brazil, Australia, Thailand", "respondent": "European Communities", "third_parties": [], "agreements": ["AA Arts. 3, 8 and 9.1"], "articles": [], "subject": "EC measures relating to subsidization of the sugar industry, namely, a Common Organization for Sugar", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Agriculture & Food السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "• EC export subsidy commitment levels for sugar: The Appellate Body upheld the Panel's finding that footnote 1 in the EC Schedule relating to preferential imports from certain ACP countries and India did not have the legal effect of enlarging or otherwise modifying the European Communities' quantity commitment level contained in Section II, Part IV of its Schedule. • AA Arts. 9.1(c), 3.3 and 8 (export subsidies – exports of C sugar): The Appellate Body upheld the Panel's finding that the European Communities violated Arts. 3.3 and 8 by exporting C sugar because export subsidies in the form of ", "keywords": ["agriculture & food", "AA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS267", "title": "US – UPLAND COTTON", "complainant": "United States", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT", "SCM"], "articles": [], "subject": "US agricultural “domestic support” measures, export credit guarantees and other measures alleged to ", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "• AA Art. 13 (due restraint (peace clause): The Appellate Body upheld the Panel's finding that the “Peace Clause” in the AA did not apply to a number of US measures, including domestic support measures for upland cotton. • ASCM Art. 6.3(c) (serious prejudice): The Appellate Body upheld the Panel's finding that the effect of subsidy programme at issue – i.e. marketing loan programme payments, Step 2 (user marketing) payments, market loss assistance payments, and counter-cyclical payments – is significant price suppression within the meaning of Art. 6.3(c), causing serious prejudice to Brazil's ", "keywords": ["agriculture & food", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS268", "title": "US – OIL COUNTRY TUBULAR GOODS SUNSET REVIEWS", "complainant": "Argentina", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 3, 6,11,12, 18 and\nAnnex"], "articles": [], "subject": "US anti-dumping duties as well as laws, regulations and practice governing sunset reviews under the", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review (ADA Art. 11.3): as such violations • SPB (DSU Art. 11): The Appellate Body upheld the Panel's finding that the SPB was a “measure” subject to WTO dispute settlement; however, due to what it considered to be an insufficient analysis, it found that the Panel had failed to make an objective assessment of the matter within the meaning of DSU Art. 11 and reversed the Panel's finding that Section II.A.3 of the SPB was inconsistent, as such, with Art. 11.3. It did not complete the analysis on this issue. • “Affirmative and deemed waiver provisions”:3 The Appellate Body upheld the Panel", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS269", "title": "EC – CHICKEN CUTS", "complainant": "Brazil, Thailand", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II"], "articles": [], "subject": "EC measures pertaining to the tariff reclassification from heading 02.10 (relating to, inter alia, s", "sector": "Other", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body upheld the Panel's ultimate finding that the EC measures (relating to tariff classification) imposed duties on the products at issue in excess of the relevant heading of the EC tariff commitment because under the EC Schedule, tariffs on frozen meat (02.07) are higher than on salted meat (02.10) and, thus, violated Arts. II:1(a) and (b). Interpretation3 of the term at issue “salted” in EC Schedule • Ordinary meaning (VCLT Art. 31(1)): The Appellate Body upheld the Panel's finding that “in essence, the ordinary meaning of the term '", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS273", "title": "KOREA – COMMERCIAL VESSELS", "complainant": "European Communities", "respondent": "Korea", "third_parties": [], "agreements": ["ASCM Arts. 3.1"], "articles": [], "subject": "Korea's various measures relating to alleged subsidies to its shipbuilding industry.2", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "ASCM Art. 3.1(a) and 3.2 (export subsidies) • Measures as such: Having found that the KEXIM legal regime (KLR), APRG and PSL programmes did not “mandate” the conferral of a “benefit,” the Panel rejected EC claims that these measures as such were inconsistent with Art. 3.1(a) and 3.2. • Measures as applied: The Panel found that certain “KEXIM guarantees” under the APRG programme were prohibited export subsidies (specific subsidies contingent upon export performance) under Art. 3.1(a) and 3.2 and rejected Korea's argument that item (j) (i.e. export credit guarantee) of the Illustrated List could", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS276", "title": "CANADA – WHEAT EXPORTS AND GRAIN IMPORTS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. XVII"], "articles": [], "subject": "Canadian Wheat Board (CWB) Export Regime2 and requirements related to the import of grain into", "sector": "Agriculture & Food", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2004", "summary_ar": "", "summary_en": "GATT Art. XVII:1 (State Trading Enterprise (STE)) • Relationship between paras. (a) and (b) of Art. XVII:1: The Appellate Body reasoned that subpara. (a) is the general and principal provision, and subpara. (b) explains it by identifying the types of differential treatment in commercial transactions that are most likely to occur in practice. Therefore, most, if not all, claims raised under Art. XVII:1 will require a sequential analysis of both subparas. (a) and (b). At the same time, because both subparas. (a) and (b) define the scope of that non-discrimination obligation, panels would not alw", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS277", "title": "US – SOFTWOOD LUMBER VI", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 3, 12 and 17\nASCM Arts. 15 and", "ASCM Arts. 15 and 22.5\nDSU Art. 11", "DSU Art. 11"], "articles": [], "subject": "Definitive anti-dumping and countervailing duties imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2004", "summary_ar": "", "summary_en": "• ADA Art. 3.7/ASCM Art. 15.7 (injury determination – threat of material injury): The Panel concluded that the International Trade Commission's (ITC) “threat of material injury” determination was inconsistent with ADA Art. 3.7 and ASCM Art. 15.7, because, in light of the totality of the factors considered and the reasoning in the ITC's determination, an objective and unbiased investigating authority could not have made a finding of a likely imminent substantial increase in imports. • ADA Art. 3.5 and 3.7/ASCM Art. 15.5 and 15.7 (injury determination – causation): The Panel found that the ITC's", "keywords": ["subsidies & anti-subsidy", "ADA", "ASCM", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS282", "title": "US – ANTI-DUMPING MEASURES ON OIL COUNTRY TUBULAR GOODS", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 3 and 11"], "articles": [], "subject": "Determinations by the United States Department of Commerce (USDOC) and the International Trade", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Art 11.3 (review of anti-dumping duties): The Appellate Body reversed the Panel's finding that the Sunset Policy Bulletin (SPB) as such was inconsistent with ADA Art. 11.3 due to the Panel's failure to make “an objective assessment of the matter and the facts of the case” as required by DSU Art. 11. The Panel initially found that the SPB established an “irrebuttable presumption” of likelihood of dumping inconsistently with ADA Art. 11.3, as the USDOC treated the standard set out in SPB as conclusive or determinative as to the “likelihood” of continuation or recurrence of dumping in “suns", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS285", "title": "US – GAMBLING", "complainant": "غير محدد", "respondent": "United States", "third_parties": [], "agreements": ["GATS Arts. XIV"], "articles": [], "subject": "Various US measures relating to gambling and betting services, including federal laws such as the “W", "sector": "Services", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "• Scope of GATS commitments: The Appellate Body upheld, based on modified reasoning, the Panel's finding that the US GATS Schedule included specific commitments on gambling and betting services. Resorting to “document W/120” and the “1993 Scheduling Guidelines”3 as “supplementary means of interpretation” under Art. 32 of the VCLT, rather than context (Art. 31), the Appellate Body concluded that the entry, “other recreational services (except sporting)”, in the US Schedule must be interpreted as including “gambling and betting services” within its scope. • GATS Art. XVI:1 and 2 (market access c", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS291", "title": "EC – APPROVAL AND MARKETING OF BIOTECH PRODUCTS", "complainant": "United States, Canada, Argentina", "respondent": "European Communities", "third_parties": [], "agreements": ["SPS Arts. 2.2, 2.3, 5.1, 5.5, 5.6, 5.7,\n"], "articles": [], "subject": "(i) Alleged general EC moratorium on approvals of biotech products; (ii) EC measures allegedly affec", "sector": "Agriculture & Food", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2006", "summary_ar": "", "summary_en": "General EC moratorium • Existence of moratorium: The Panel found that a general de facto moratorium on approvals of biotech products was in effect on the date of panel establishment, i.e., August 2003. It was general in that it applied to all applications for approval pending in August 2003 under the relevant EC legislation, and de facto because it had not been formally adopted. Approvals were prevented through actions/omissions by a group of five EC member States and/or the European Commission. • SPS Arts. 5.1 (risk assessment) and 2.2 (sufficient scientific evidence): The Panel found that th", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS294", "title": "US – ZEROING (EC)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 9.3, 2.4 and 2.4.2\nGATT Art. V", "GATT Art. VI"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in determining dumping margins in anti-dumping", "sector": "Anti-Dumping", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2006", "summary_ar": "", "summary_en": "As applied claims • ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that the zeroing methodology, as applied by the United States in the administrative reviews at issue, was inconsistent with ADA Art. 9.3 and GATT Art. VI:2, as it resulted in amounts of anti-dumping duties that exceeded the foreign producers’ or exporters’ margins of dumping. Under ADA Art. 9.3 and GATT Art. VI:2, investigating authorities are required to ensure that the total amount of anti-dumping duties collected on the entries of a product fr", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS295", "title": "MEXICO – ANTI-DUMPING MEASURES ON RICE", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["ADA Arts. 3, 5.8, 6, 9, 11 12 and 17"], "articles": [], "subject": "Mexico's definitive anti-dumping duties; several provisions of Mexico's Foreign Trade Act; and the F", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 3.1, 3.2, 3.4 and 3.5 (injury determination – period for the injury investigation): The Appellate Body upheld the Panel's finding that Mexico violated Arts. 3.1, 3.2, 3.4 and 3.5, as it based its determination of injury on a period of investigation which ended more than 15 months before the initiation of the investigation, and thus it had failed to make an injury determination based on positive evidence, and involving an objective examination of the volume and price effects of the alleged dumped imports or the impact of the imports on domestic producers at the time measures were im", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS296", "title": "US – COUNTERVAILING DUTY INVESTIGATION ON DRAMS", "complainant": "United States", "respondent": "Korea", "third_parties": [], "agreements": ["SCM"], "articles": [], "subject": "US final countervailing duty order on imports from Korea.", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1)(iv) (definition of a subsidy – “entrusts” or “directs”): The Panel found that the ordinary meanings of “entrusts” and “directs” must contain a notion of delegation or command. The Appellate Body explained that although “direction””or “command” are two means by which a government may provide a financial contribution, the scope of actions covered by “entrustment” and “delegation” could extend beyond what is covered by the terms “direction” and “command” if strictly construed. It explained that “entrustment” occurs where a government gives responsibility to a private body, a", "keywords": ["subsidies & anti-subsidy", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS299", "title": "EC – COUNTERVAILING MEASURES ON DRAM CHIPS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 12, 14 and 15"], "articles": [], "subject": "EC definitive countervailing duties.", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1)(iv) (definition of a subsidy – financial contribution): The Panel held that the European Communities' “financial contribution” finding with respect to one of Korea's five alleged subsidy programmes3 was inconsistent with Art. 1.1(a) (1)(iv), as it considered that the evidence before the EC investigating authority (i.e. government official's presence at Hynix's Creditor Council meeting) was insufficient for it to reasonably conclude that the Korean government entrusted or directed the private banks to purchase Hynix convertible bonds. The Panel held that the European Commu", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS301", "title": "EC – COMMERCIAL VESSELS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. III", "DSU Art. 23.1"], "articles": [], "subject": "The European Communities' Temporary Defensive Mechanism for Shipbuilding (the “TDM Regulation”)", "sector": "Other", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Arts. III:4 (national treatment – domestic laws and regulations) and III:8(b) (national treatment – subsidies exception): The Panel concluded that the state aid subject to the TDM Regulation was covered by GATT Art. III:8(b) because it provided for “the payment of subsidies exclusively to domestic producers”, and therefore the TDM Regulation, the national TDM schemes (in this case, Denmark, France, Germany, the Netherlands and Spain) and the EC decisions authorizing the schemes were not inconsistent with GATT Art. III:4. • GATT Arts. I:1 (most-favoured-nation treatment) and III:8(b) (na", "keywords": ["other", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS302", "title": "DOMINICAN REPUBLIC – IMPORT AND SALE OF CIGARETTES", "complainant": "Honduras", "respondent": "Dominican Republic", "third_parties": [], "agreements": ["GATT Arts. II, III", "DSU Art. 19"], "articles": [], "subject": "Dominican Republic's general measures relating to import charges and fees and other measures specifi", "sector": "Other", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2005", "summary_ar": "", "summary_en": "Stamp requirement • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the stamp requirement, which required tax stamps to be affixed to cigarette packets in the Dominican Republic, “accords less favourable treatment to imported cigarettes than that accorded to the like domestic products, contrary to GATT Art. III:4”. The Appellate Body upheld the Panel's finding that this requirement was not necessary within the meaning of Art. XX(d) as, inter alia, there were “reasonably available” alternative WTO-consistent measures and, thus, the measure was not just", "keywords": ["other", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS308", "title": "MEXICO – TAXES ON SOFT DRINKS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATT Arts. III and XX"], "articles": [], "subject": "Mexico's tax measures under which soft drinks using non-cane sugar sweeteners were subject to", "sector": "Agriculture & Food", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2006", "summary_ar": "", "summary_en": "National treatment • GATT Arts. III:2 (national treatment – taxes and charges), first sentence (like products): As for soft drinks sweetened with HFCS, the Panel found that the tax measures were inconsistent with Art. III:2, first sentence, as these drinks were subject to internal taxes (20 per cent transfer and services taxes) in excess of taxes imposed on like domestic products – i.e. soft drinks sweetened with cane sugar (exemption from those taxes). • GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): As for non-cane ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS312", "title": "KOREA – CERTAIN PAPER", "complainant": "Indonesia", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6, 9, 12 and Annex II"], "articles": [], "subject": "Anti-dumping duties imposed by Korea on certain imports.", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 2,2, 6.8 and Annex II(3) (dumping determination – facts availabe): The Panel found that the Korean investigating authority (i.e. KTC) did not act inconsistently with Art. 6.8 and Annex II(3) when it resorted to facts available for the calculation of normal value for two Indonesian exporters because the information requested (financial statements and accounting records) had not been submitted “within a reasonable period of time”. In addition, the data submitted to the KTC after the deadline were not verifiable within the meaning of Annex II(3) in light of the fact that the exporters", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS315", "title": "EC – SELECTED CUSTOMS MATTERS", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "The European Communities' administration of various customs laws and regulations, and the omission", "sector": "Other", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2006", "summary_ar": "", "summary_en": "Panel's terms of reference • Measure at issue (Art. X:3(a)): The Appellate Body reversed the Panel's finding that when a violation of GATT Art. X:3(a) is being claimed, the “measure at issue” must be the “manner of administration” of a legal instrument; a WTO Member is not precluded from setting out in a panel request any act or omission attributable to another WTO Member as the measure at issue. • The European Communities' system as a whole: The Panel rejected the United States' Art. X:3(a) challenge of the European Communities' customs administration overall, on the grounds, inter alia, that", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS316", "title": "EC AND CERTAIN MEMBER STATES – LARGE CIVIL AIRCRAFT", "complainant": "United States", "respondent": "European Union", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 3.1, 3.2, 5, 6.3,\n6.4, ", "GATT 1994 Arts. III"], "articles": [], "subject": "Subsidies & Anti-Subsidy", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Arts. 1 and 2 (financial contribution, benefit, specificity): The Appellate Body upheld the Panel’s findings that Airbus paid a lower interest rate for the A350XWB LA/MSF than would have been available to it on the market and, consequently, a benefit was thereby conferred within the meaning of Art. 1.1(b). Consequently, the Appellate Body also upheld the Panel’s findings that the A350XWB LA/MSF measures were specific subsidies within the meaning of Arts. 1 and 2. • ASCM Art. 3.1(a) and (b) (prohibited subsidies): The Panel rejected the United States’ claims that the A380 and A350XWB LA/", "keywords": ["subsidies & anti-subsidy", "ASCM", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS320", "title": "US – CONTINUED SUSPENSION", "complainant": "European Communities", "respondent": "غير محدد", "third_parties": [], "agreements": ["DSU Arts. 22.8, 23.1, 23.2", "SPS Arts. 5.1 and 5.7"], "articles": [], "subject": "The continued suspension of WTO concessions by the United States and Canada resulting from the EC –", "sector": "Agriculture & Food", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2008", "summary_ar": "", "summary_en": "• DSU Arts. 23.1 (prohibition on unilateral determinations) and 3.7 read together with Art. 22.8 (duration of suspension): The Appellate Body upheld the Panels' finding that the European Communities had not established a violation of DSU Arts. 23.1 and 3.7 as a result of a breach of Art. 22.8, because it was not established that the measure found to be inconsistent with the SPS Agreement in the EC – Hormones dispute had been removed. • DSU Arts. 23.1 and 23.2(a) (prohibition on unilateral determinations – maintaining suspension of concessions): The Appellate Body reversed the Panels' finding t", "keywords": ["agriculture & food", "DSU", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS322", "title": "US – ZEROING (JAPAN)", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 9 and 11\nGATT Arts. VI", "GATT Arts. VI"], "articles": [], "subject": "The United States' “zeroing” procedures in the context of original investigations, periodic reviews,", "sector": "Anti-Dumping", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2007", "summary_ar": "", "summary_en": "As such claims • ADA Arts. 2.1, 2.4 and 2.4.2 and GATT Arts. VI:1 and VI:2 (zeroing in transaction-to-transaction comparisons in original investigations): The Appellate Body reversed the Panel's finding that the United States did not act inconsistently with Arts. 2.1, 2.4, and 2.4.2 by maintaining zeroing procedures in original investigations when calculating margins of dumping on the basis of transaction-to-transaction comparisons. The Appellate Body noted that because dumping and margins of dumping can only be found to exist in relation to the product under investigation, and not at the leve", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS331", "title": "MEXICO – STEEL PIPES AND TUBES", "complainant": "Guatemala", "respondent": "Mexico", "third_parties": [], "agreements": ["GATT", "ADA"], "articles": [], "subject": "The definitive anti-dumping duties imposed by Mexico on imports of steel pipes and tubes from Guatem", "sector": "Metals & Mining", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2007", "summary_ar": "", "summary_en": "A. The Panel found that the Investigating Authority “IA” acted inconsistently with Mexico's obligations under: • ADA Arts. 5.3 and 5.8 (initiation and subsequent investigation): in its assessment of the sufficiency of evidence of dumping and injury to justify the initiation of the investigation and, consequently, its failure to reject the application in the absence of sufficient evidence to justify proceeding with the investigation. • ADA Arts. 3.1, 3.2, 3.4 and 3.5 (injury determination): (i) in relying, without sufficient justification, on injury data limited to three six-month periods over ", "keywords": ["metals & mining", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS332", "title": "BRAZIL – RETREADED TYRES", "complainant": "European Communities", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I"], "articles": [], "subject": "(i) Brazil's import prohibition on retreaded tyres (Import Ban); (ii) fines on importing, marketing,", "sector": "Other", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2007", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel concluded that Brazil's import prohibition on retreaded tyres and the fines imposed by Brazil on importation, marketing, transportation, storage, keeping or warehousing of retreaded tyres were inconsistent with Art. XI:1. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure maintained by the Brazilian State of Rio Grande do Sul in respect of retreaded tyres, Law 12.114, as amended by Law 12.381, was inconsistent with Art. III:4. • GATT Art. XX(b) (general exceptions – necess", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS334", "title": "TURKEY – RICE", "complainant": "Turkey", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. III"], "articles": [], "subject": "Turkey's restrictions on the importation of rice, in particular: (i) the decision, during specific p", "sector": "Agriculture & Food", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2007", "summary_ar": "", "summary_en": "• AA Art. 4.2 (quantitative restrictions): The Panel found that Turkey had denied or failed to grant licences to import rice at the most-favoured-nation tariff rates, i.e. outside the tariff rate quotas. This was found by the Panel to be a quantitative import restriction and discretionary import licensing, within the meaning of footnote 1 to Art. 4.2.2 • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that Turkey's requirement that importers purchase domestic rice in order to be allowed to import rice under the tariff rate quotas, was inconsistent with Art", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS335", "title": "US – SHRIMP (ECUADOR)", "complainant": "Ecuador", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States' final anti-dumping measures including margins of dumping calculated using “zeroing” u", "sector": "Agriculture & Food", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2007", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel found that the United States Department of Commerce “USDOC” acted inconsistently with the first sentence of Art. 2.4.2 by using “zeroing” in calculating margins of dumping under the weighted-average-to-weighted-average methodology in the context of an original investigation.", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS336", "title": "JAPAN – DRAMS (KOREA)", "complainant": "Japan", "respondent": "Korea", "third_parties": [], "agreements": ["SCM"], "articles": [], "subject": "Japanese investigation of and final countervailing duty order on imports from Korea.", "sector": "Subsidies & Anti-Subsidy", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2007", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1)(iv) (definition of a subsidy – entrustment or direction): Having rejected one of the intermediary findings relied on by the Japanese investigating authorities (JIA) for finding “entrustment and direction” by the Korean government (namely, the commercial reasonableness of some Hynix creditors participating in certain restructuring transactions in December 2002), the panel found that the JIA's overall determination was thereby flawed. The Appellate Body found that the Panel had failed to comply with the required standard of review under DSU Art. 11 because it did not examin", "keywords": ["subsidies & anti-subsidy", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS337", "title": "EC – SALMON (NORWAY)", "complainant": "Norway", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT", "ADA"], "articles": [], "subject": "EC definitive anti-dumping measures on imports of farmed salmon from Norway.", "sector": "Agriculture & Food", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2008", "summary_ar": "", "summary_en": "• ADA Arts. 2.1, 2.6 and 4.1 (dumping determination – product and domestic industry): The Panel concluded that Arts 2.1 and 2.6 did not require the European Communities to have defined the product under consideration to include only products that are all “like”, and do not establish an obligation on investigating authorities to ensure that where the product under consideration is made up of categories of products, all such categories of products are individually “like” each other, thereby constituting a single “product”. The Panel found that the exclusion of certain categories of economic oper", "keywords": ["agriculture & food", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS339", "title": "CHINA – AUTO PARTS", "complainant": "Canada, China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. II, III"], "articles": [], "subject": "Three legal instruments enacted by China2 which impose a 25 per cent “charge” 3 on imported auto par", "sector": "Automotive", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2009", "summary_ar": "", "summary_en": "• “Ordinary customs duty” vs “internal charge”: As a preliminary “threshold” issue, the Appellate Body upheld the Panel's characterization of the charge as an “internal charge” (Art. III:2), rather than as an “ordinary customs duty” (first sentence, Art. II:1(b)), because, after considering the characteristics of the measure, the Panel had properly ascribed legal significance to, inter alia, the fact, that the obligation to pay the charge accrues internally, after auto parts enter China. • GATT Arts. III:2 (national treatment – taxes and charges) and III:4 (national treatment – domestic laws a", "keywords": ["automotive", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS341", "title": "MEXICO – OLIVE OIL", "complainant": "Mexico", "respondent": "European Communities", "third_parties": [], "agreements": ["SCM"], "articles": [], "subject": "Countervailing duties on olive oil from the European Communities.", "sector": "Subsidies & Anti-Subsidy", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2008", "summary_ar": "", "summary_en": "• ASCM Art. 11.11 (duration of investigation): Economía (the investigating authority) acted inconsistently with Art. 11.11, because the investigation exceeded the 18-month maximum time-limit set forth therein. • ASCM Art.12.4 (evidence – disclosure of information): Economía failed to comply with the requirement in Art. 12.4.1 to require interested parties to submit non-confidential summaries of confidential information, or in exceptional circumstances, to explain why summarization is impossible. Blanket statements are insufficient for such explanations. • ASCM Art. 12.8 (evidence – disclosure ", "keywords": ["subsidies & anti-subsidy", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS343", "title": "US – SHRIMP (THAILAND), US – CUSTOMS BOND DIRECTIVE", "complainant": "United States, India", "respondent": "Thailand", "third_parties": [], "agreements": ["ADA Arts. 18.1\nGATT Ad Art.VI paras. 2 a", "GATT Ad Art.VI paras. 2 and 3,\nArt. XX"], "articles": [], "subject": "The enhanced continuous bond requirement (EBR).", "sector": "Agriculture & Food", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2008", "summary_ar": "", "summary_en": "• ADA Art. 18.1 and GATT Ad Art. VI, paras. 2 and 3: (“Specific action against dumping”): The Panel found that the EBR, as applied, constituted “specific action against dumping”. The Appellate Body did not express a view on this finding as it was not appealed. (“Temporal scope”): The Appellate Body followed the Panel's approach in considering first whether the EBR had been taken “in accordance with the provisions of the GATT 1994”, in particular, GATT Ad Art. VI, paras. 2 and 3. The Appellate Body preliminarily determined the temporal scope of the Ad Note, and agreed with the Panel that the ph", "keywords": ["agriculture & food", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS344", "title": "US – STAINLESS STEEL (MEXICO)", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 9.3\nGATT Art. VI", "GATT Art. VI"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in anti-dumping proceedings as well as the zer", "sector": "Metals & Mining", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2008", "summary_ar": "", "summary_en": "• ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that zeroing in administrative reviews is, as such, inconsistent with GATT Art. VI:2 and ADA Art. 9.3 because it results in the levying of anti-dumping duties that exceed the exporter's or foreign producer's margin of dumping – which operates as a ceiling for the amount of anti-dumping duties that can be levied in respect of the sales made by an exporter. The Appellate Body saw no basis in GATT Arts. VI:1 and VI:2 or in ADA Arts. 2 and 9.3 for disregarding the res", "keywords": ["metals & mining", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS350", "title": "US – CONTINUED ZEROING", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Arts. 6.2 and 11\nADA Arts. 2.4.2, 9.", "ADA Arts. 2.4.2, 9.3, 11.3 and\n17.6"], "articles": [], "subject": "The European Communities challenged as a measure the ongoing application by the United States of ant", "sector": "Anti-Dumping", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2009", "summary_ar": "", "summary_en": "• ADA Art. 9.3, GATT Art. VI:2 and ADA Art. 11.3 (ongoing application of anti-dumping duties calculated with zeroing): The Appellate Body reversed the Panel's finding that the European Communities failed in its request for panel establishment to identify the measure in 18 anti-dumping cases. The Appellate Body found that the panel request identified the specific measures at issue as the continued application of anti-dumping duties calculated with the use of the zeroing methodology in each of the 18 cases listed in the annex to the panel request. The Appellate Body considered these measures to ", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS353", "title": "US – LARGE CIVIL AIRCRAFT (2ND COMPLAINT)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 3.1", "DSU Arts. 6.2 and 11"], "articles": [], "subject": "Subsidies allegedly granted by US federal, state and local governments to Boeing large civil aircraf", "sector": "Subsidies & Anti-Subsidy", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2012", "summary_ar": "", "summary_en": "• ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): The Panel upheld the EC claim that FSC-related subsidies provided to Boeing were inconsistent with Art. 3.1(a), but rejected the EC claim that certain Washington State tax measures were contingent upon export performance. These findings were not appealed. • ASCM Arts. 5(c) and 6.3 (serious prejudice – displacement, lost sales and price suppression): The Appellate Body agreed with the Panel, although for different reasons, that the NASA and USDOD measures enabled Boeing to launch its technologically advanced 787 in 2004, thereby caus", "keywords": ["subsidies & anti-subsidy", "ASCM", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS360", "title": "INDIA – ADDITIONAL IMPORT DUTIES", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. II"], "articles": [], "subject": "Two border charges, consisting of the “Additional Duty” imposed by India on imports of alcoholic bev", "sector": "Other", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2008", "summary_ar": "", "summary_en": "• GATT Arts. II:1(b) and II:2(a) (schedules of concessions): The Appellate Body reversed the Panel's finding that the United States had failed to establish that the Additional Duty and the Extra-Additional Duty were inconsistent with Arts. II:1(b) and II:2(a). The Appellate Body explained that it did not see a textual or other basis for the Panel's conclusion that “inherent discrimination” is a relevant or necessary feature of charges covered by Art. II:1(b). The Appellate Body further found that the Panel erred in its interpretation of the two elements of Art. II:2(a), that is “equivalence” a", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS362", "title": "CHINA – INTELLECTUAL PROPERTY RIGHTS", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["TRIPS"], "articles": [], "subject": "(i)", "sector": "Intellectual Property", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2009", "summary_ar": "", "summary_en": "• TRIPS Art. 61 (border measures – remedies): The Panel found that while China's criminal measures exclude some copyright and trademark infringements from criminal liability where the infringement falls below numerical thresholds fixed in terms of the amount of turnover, profit, sales or copies of infringing goods, this fact alone was not enough to find a violation because Art. 61 does not require Members to criminalize all copyright and trademark infringement. The Panel found that the term “commercial scale” in Art. 61 meant “the magnitude or extent of typical or usual commercial activity wit", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS363", "title": "CHINA – PUBLICATIONS AND AUDIOVISUAL PRODUCTS", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT", "GATS"], "articles": [], "subject": "A series of Chinese measures regulating activities relating to the importation and distribution of c", "sector": "Services", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2010", "summary_ar": "", "summary_en": "• China's Accession Protocol (China's trading rights commitments): The Panel found that provisions in China's measures that either limit to wholly State-owned enterprises importation rights regarding, or prohibit foreign-invested enterprises in China from importing, reading materials, AVHE products, sound recordings, and films, were inconsistent with China's obligation, under paras. 1.2 and 5.1 of China's Accession Protocol and paras. 83(d) and 84(a) of China's Accession Working Party Report, to grant the right to trade. The Panel also concluded that several provisions of the Chinese measures ", "keywords": ["services", "GATT", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS366", "title": "COLOMBIA – PORTS OF ENTRY", "complainant": "Colombia", "respondent": "Panama", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Colombian customs regulations establishing the use of indicative prices and restrictions on ports of", "sector": "Agriculture & Food", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2009", "summary_ar": "", "summary_en": "• CVA Arts. 1, 2, 3, 5, 6 and 7.2(b) and (f) (sequential use of valuation methods): The Panel found that Colombia's use of indicative prices constituted customs valuation and that the measures establishing indicative prices, by mandating their use for customs valuation purposes, were inconsistent as such with the obligation established in the CVA to apply, in a sequential manner, the methods of valuation provided in Arts. 1, 2, 3, 5 and 6 of the Agreement. The Panel further found that, by mandating the use of the higher of two values, or a minimum price as the customs value of subject goods, t", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS367", "title": "AUSTRALIA – APPLES", "complainant": "New Zealand", "respondent": "Australia", "third_parties": [], "agreements": ["SPS Arts. 2.2, 2.3, 5.1, 5.2, 5.5, 5.6,\n", "DSU Art. 11"], "articles": [], "subject": "Certain Australian measures restricting the importation of New Zealand apples based on concerns", "sector": "Agriculture & Food", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2010", "summary_ar": "", "summary_en": "• SPS Annex A(1) (SPS measures): The Appellate Body upheld the Panel's finding that the 16 measures at issue, both as a whole and individually, constituted SPS measures within the meaning of Annex A(1) to the SPS Agreement. • SPS Arts. 2.2, 5.1 and 5.2 (risk assessment): The Panel found that specific measures regarding each of the three pests at issue, as well as the “general” measures relating to these three pests, were inconsistent with Arts. 5.1 and 5.2, and that, by implication, these measures were also inconsistent with Art. 2.2 of the SPS Agreement. Australia appealed these findings only", "keywords": ["agriculture & food", "SPS", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS371", "title": "THAILAND – CIGARETTES (PHILIPPINES)", "complainant": "Thailand", "respondent": "Philippines", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Thailand's customs and tax measures.", "sector": "Other", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2011", "summary_ar": "", "summary_en": "• CVA Art. 1.1 and 1.2(a) (valuation in a related-party transaction): In determining the acceptability of the transaction value declared by the importer in a related-party transaction, customs authorities must (i) examine the circumstances of the sale in the light of the information provided by the importer or otherwise; (ii) communicate to the importer the grounds for preliminarily considering that the relationship influenced the price; and (iii) give the importer a reasonable opportunity to respond so that the importer can submit further information. The Panel found that Thai Customs acted i", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS375", "title": "EC – IT PRODUCTS", "complainant": "United States, Japan, Taipei", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. II"], "articles": [], "subject": "Various EC measures pertaining to the tariff classification, and consequent tariff treatment, of cer", "sector": "Other", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2010", "summary_ar": "", "summary_en": "• The Ministerial Declaration on Trade in Information Technology Products (ITA): The European Communities had committed in its WTO Schedule to provide duty‑free treatment to certain IT products pursuant to the ITA. The products receiving duty-free treatment were indicated in the ITA in two ways: as HS1996 headings and in “narrative description” form. • GATT Arts. II:1(a) and II:1(b) (schedules of concessions – FPDs): The Panel found that the measures at issue were inconsistent with Arts. II:1(a) and II:1(b) because they required EC member States to classify some FPDs under dutiable headings al", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS379", "title": "US – ANTI-DUMPING AND COUNTERVAILING DUTIES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 2.1, 2.2, 10, 12, 14,\n19", "GATT Art. I, VI"], "articles": [], "subject": "Countervailing and anti-dumping measures imposed concurrently by the United States against the same", "sector": "Subsidies & Anti-Subsidy", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2011", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of a subsidy – public body): The Appellate Body reversed the Panel's interpretation of the term “public body” in ASCM Art. 1.1(a)(1) and found that a public body is an entity that possesses, exercises, or is vested with, governmental authority. The Appellate Body completed the analysis and found that the United States had acted inconsistently with ASCM Arts. 1.1(a)(1), 10, and 32.1 in finding that certain State-owned enterprises (SOEs) constituted public bodies. It also found that China did not establish that the USDOC had acted inconsistently with Art. 1.1(a)", "keywords": ["subsidies & anti-subsidy", "ASCM", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS381", "title": "US – TUNA II (MEXICO)", "complainant": "غير محدد", "respondent": "United States", "third_parties": [], "agreements": ["GATT", "TBT"], "articles": [], "subject": "(1) United States Code, Title 16, Section 1385 – “Dolphin Protection Consumer Information Act” (DPCI", "sector": "Standards & TBT", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (definition of technical regulation): The Appellate Body found that “the US measure establishes a single and legally mandated set of requirements for making any statement with respect to the broad subject of ‘dolphin-safety’ of tuna products in the United States”. Thus, it upheld the Panel’s ruling characterizing the measure at issue as a “technical regulation” within the meaning of TBT Annex 1. • TBT Art. 2.1 (national treatment – technical regulations): According to the Appellate Body, the measure at issue modified the competitive conditions in the US market to the detriment ", "keywords": ["standards & tbt", "GATT", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS382", "title": "US – ORANGE JUICE (BRAZIL)", "complainant": "Brazil", "respondent": "United States", "third_parties": [], "agreements": ["ADA. Art 2.4"], "articles": [], "subject": "United States Department of Commerce's (USDOC) (i) use of zeroing in two administrative reviews and ", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (dumping determination – fair comparison): The Panel concluded that the use of zeroing to determine margins of dumping and importer-specific assessment rates was inconsistent with Art. 2.4 because it involves a comparison between export price and normal value that will invariably result in a higher margin of dumping than would otherwise be the case. In reaching this conclusion, the Panel clarified that, for systemic reasons, it followed the Appellate Body's previous findings on the United States' use of zeroing in anti-dumping proceedings. The Panel found that the United States ", "keywords": ["anti-dumping", "ADA."], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS383", "title": "US – ANTI-DUMPING MEASURES ON PET BAGS", "complainant": "United States", "respondent": "Thailand", "third_parties": [], "agreements": ["ADA"], "articles": [], "subject": "Anti-dumping order imposed by the United States on polyethylene retail carrier bags from Thailand, a", "sector": "Anti-Dumping", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2010", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel upheld Thailand's claim that the use of zeroing by the USDOC in the calculation of the margins of dumping in respect of the measures at issue was inconsistent with the United States' obligations under because the USDOC did not calculate these dumping margins on the basis of the “product as a whole”, taking into account all comparable export transactions in calculating the margins of dumping. • DSU Art. 19.1 (Panel and Appellate Body recommendations – suggestion on implementation): Consistent with the first sentence of Art. 19.1, the", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS384", "title": "US – COOL", "complainant": "Canada, Mexico", "respondent": "United States", "third_parties": [], "agreements": ["TBT Arts. 2.1, 2.2, 2.4, 12.1 and\n12.3, ", "GATT Arts. III"], "articles": [], "subject": "United States’ country of origin labelling (COOL) requirements for beef and pork contained in the", "sector": "Agriculture & Food", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• TBT Art. 2.1 (national treatment – technical regulations): The Appellate Body upheld, albeit for modified reasons, the Panel’s finding that the COOL measure was inconsistent with Art. 2.1 because it accorded less favourable treatment to imported livestock than to like domestic livestock. The Appellate Body concluded that the least costly way of complying with the COOL measure was to rely exclusively on domestic livestock, creating an incentive for US producers to use exclusively domestic livestock and thus causing a detrimental impact on the competitive opportunities of imported livestock. T", "keywords": ["agriculture & food", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS396", "title": "PHILIPPINES – DISTILLED SPIRITS", "complainant": "United States", "respondent": "European Union", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Philippines excise tax on distilled spirits, which imposed different tax rates depending on the raw ", "sector": "Other", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel’s finding that each type of imported distilled spirit at issue in this dispute – gin, brandy, vodka, whisky, and tequila – made from non-designated raw materials was “like” the same type of domestic distilled spirit made from designated raw materials, within the meaning of Art. III:2, first sentence. Accordingly, the Appellate Body upheld the Panel’s finding that, through its excise tax, the Philippines subjected specific types of imported distilled spirits to interna", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS397", "title": "EC – FASTENERS (CHINA)", "complainant": "China", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.4, 4.1, 6.2, 6.4, 6.5,\n6.10,"], "articles": [], "subject": "(i) Art. 9(5) of the European Union's basic anti-dumping regulation (Basic AD Regulation), concernin", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Arts. 6.10 (evidence – individual dumping margins) and 9.2 (imposition of anti-dumping duties – individual exporters or producers): The Appellate Body upheld, although for different reasons, the Panel's findings that Art. 9(5) of the Basic AD Regulation was inconsistent as such and as applied in the fasteners investigation with Arts. 6.10 and 9.2 because it conditioned the granting of individual treatment to exporters or producers from NMEs in the determination and imposition of anti-dumping duties on the fulfilment of the individual treatment test. The Appellate Body found that Arts. 6.", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS399", "title": "US – TYRES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "US transitional product-specific safeguard measure applied under para. 16 of China's Accession Proto", "sector": "Safeguards", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2011", "summary_ar": "", "summary_en": "• China's Accession Protocol, para. 16.4 (imports “increasing rapidly”): The Appellate Body upheld the Panel's finding that the United States International Trade Commission (USITC) properly established that imports of subject tyres from China met the “increasingly rapidly” threshold provided in para. 16.4. The Appellate Body reasoned that such increases in imports must be occurring over a short and recent period of time, and must be of a sufficient magnitude in relative or absolute terms so as to be a significant cause of material injury to the domestic industry. • China's Accession Protocol, ", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS400", "title": "EC – SEAL PRODUCTS", "complainant": "Canada, Norway", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Arts. 2.1, 2.2, 5.1.2, and 5.2.1\nGAT", "GATT Arts. I"], "articles": [], "subject": "Regulations of the European Union (EU Seal Regime) generally prohibiting the importation and placing", "sector": "Standards & TBT", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2014", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (technical regulation): The Appellate Body reversed the Panel’s intermediate finding that the EU Seal Regime lays down “product characteristics”, and consequently reversed the Panel’s finding that the EU Seal Regime was a “technical regulation” within the meaning of TBT Annex 1.1. The Appellate Body was unable to complete the legal analysis and thus did not rule on whether the EU Seal Regime lays down “related processes and production methods” within the meaning of TBT Annex 1.1. The Appellate Body therefore declared moot and of no legal effect the Panel’s conclusions under TBT", "keywords": ["standards & tbt", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS402", "title": "US – ZEROING (KOREA)", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "Certain United States final determinations and anti-dumping duty orders that included margins of dum", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – fair comparison): The Panel found that the United States acted inconsistently with the first sentence of Art. 2.4.2 by using the zeroing methodology in calculating certain margins of dumping in the context of the three original investigations at issue.", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS404", "title": "US – SHRIMP (VIET NAM)", "complainant": "غير محدد", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2.1, 2.4, 2.4.2, 6.10,\n6.10.2,", "GATT Art. VI"], "articles": [], "subject": "Second and third administrative review determinations in anti-dumping proceedings against imports fr", "sector": "Agriculture & Food", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (dumping determination – zeroing, as applied): The Panel found that the USDOC's use of zeroing in the calculation of dumping margins was inconsistent with Art. 2.4. • ADA Art. 9.3 and GATT Art. VI:2 (imposition of anti-dumping duties – zeroing, as such): The Panel found that Viet Nam had established the existence of the “zeroing methodology” as a rule or norm of general and prospective application maintained by the USDOC. Relying on prior Appellate Body rulings, the Panel concluded that simple zeroing in administrative reviews is, as such, inconsistent with Art. 9.3 and Art. VI:", "keywords": ["agriculture & food", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS405", "title": "EU – FOOTWEAR (CHINA)", "complainant": "China", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.2, 6.5, 6.10, 9.2 and\n18.4"], "articles": [], "subject": "(1) Art. 9.5 of the European Union’s basic anti-dumping regulation (Basic AD Regulation), regulating", "sector": "Anti-Dumping", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2012", "summary_ar": "", "summary_en": "Claims related to the treatment of NMEs • ADA Arts. 6.10, 9.2, 18.4 and WTO Agreement Art. XVI:4 (individual treatment in imposing anti-dumping duties): ADA Arts. 6.10 and 9.2 support the same basic principle that individual exporters and producers in anti-dumping investigations should be treated individually in the determination and imposition of anti-dumping duties, except where it would be impracticable to do so. The Panel thus found that Art. 9.5 of the Basic AD Regulation was as such and as applied inconsistent with both of these provisions because, for NMEs, it imposed duties for produce", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS406", "title": "US – CLOVE CIGARETTES", "complainant": "Indonesia", "respondent": "United States", "third_parties": [], "agreements": ["TBT"], "articles": [], "subject": "Section 907(a)(1)(A) of the Federal Food, Drug, and Cosmetic Act (Section 907(a)(1)(A)), a tobacco c", "sector": "Agriculture & Food", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• TBT Art. 2.1 (no less favourable treatment): The Appellate Body upheld, although for different reasons, the Panel’s finding that clove cigarettes imported from Indonesia and menthol cigarettes produced in the United States were “like products” within the meaning of Art. 2.1. The Appellate Body disagreed with the Panel that the concept of “like products” in Art. 2.1 should be interpreted based on the regulatory purpose of the technical regulation at issue. Instead, the Appellate Body considered that the determination of whether products are “like” within the meaning of Art. 2.1 is a determina", "keywords": ["agriculture & food", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS412", "title": "CANADA – RENEWABLE ENERGY/", "complainant": "European Union, Canada", "respondent": "Japan", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "Subsidies & Anti-Subsidy", "sector": "Subsidies & Anti-Subsidy", "year": 2013, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2013", "summary_ar": "", "summary_en": "• Relationship between the TRIMs Agreement and GATT: In the dispute between Canada and the European Union, the Appellate Body upheld the Panel's finding that para. 1(a) of the Illustrative List in the Annex to the TRIMs Agreement did not obviate the need for the Panel to undertake an analysis of whether the challenged measures are outside of the scope of application of GATT Art. III:4 by virtue of the operation of GATT Art. III:8(a). • GATT Art. III:8(a) (national treatment – derogation): Both the Panel and the Appellate Body found, albeit for different reasons, that the measures at issue did ", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS413", "title": "CHINA – ELECTRONIC PAYMENT SERVICES", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATS Arts. XVI and XVII"], "articles": [], "subject": "Services", "sector": "Services", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• Classification of the services at issue: The Panel found that electronic payment services for payment card transactions are classifiable under Subsector 7.B(d) of China’s Services Schedule, which reads “[a]ll payment and money transmission services, including credit, charge, and debit cards, travellers cheques and bankers drafts (including import and export settlement)”. It observed that the use of the term “all” manifests an intention to cover the entire spectrum of the “payment and money transmission services” encompassed under Subsector (d). • Scope of China’s GATS commitments: The Panel ", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS414", "title": "CHINA – GOES", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "China’s imposition of anti-dumping and countervailing duties on grain oriented flat-rolled electrica", "sector": "Metals & Mining", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2012", "summary_ar": "", "summary_en": "• ASCM Arts. 11.2 and 11.3 (initiation of investigation – application): The Panel concluded that the obligation upon Members in relation to the assessment of the sufficiency of evidence in an application finds expression in Art. 11.3 and must be read together with Art. 11.2, which sets forth the requirements for sufficient evidence. The Panel found that MOFCOM initiated countervailing duty investigations into 11 programmes without sufficient evidence to justify it, contrary to Art. 11.3. • ADA Art. 6.8 and Annex II para. 1/ASCM Art. 12.7 (evidence – facts available): The Panel found that MOFCO", "keywords": ["metals & mining", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS415", "title": "DOMINICAN REPUBLIC – SAFEGUARD MEASURES", "complainant": "Guatemala, Honduras, Dominican Republic", "respondent": "Costa Rica", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "The provisional and final safeguard measures imposed by the Dominican Republic on imports, and the", "sector": "Safeguards", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2012", "summary_ar": "", "summary_en": "• GATT Arts. I:1 (most-favoured-nation treatment) and II:1(b) (schedules of concessions – other duties or charges): The Panel concluded that the measures at issue had the effect of suspending the Dominican Republic’s most-favoured-nation treatment obligation in Art. I:1, as well as the prohibition on other duties or charges in connection with importation within the meaning of Art. II:1(b). • GATT Art. XIX:1(a) (applicability of emergency action on imports of particular products): As a consequence, the Panel concluded that the measures suspended the Dominican Republic’s obligations under GATT w", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS422", "title": "US – SHRIMP AND SAWBLADES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States anti-dumping measures covering two products from China.", "sector": "Agriculture & Food", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2012", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel upheld China’s claim that the use of zeroing in calculating the margins of dumping in the anti-dumping investigations at issue was inconsistent with Art. 2.4.2, and therefore concluded that the United States had acted inconsistently with its obligations under this provision. ADA Art. 2.4.2 (dumping determination – separate rate calculation): The Panel rejected China’s claim concerning the separate rate in the shrimp investigation. As the investigation concerned imports from a non-market economy, the United States Department of Comme", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS425", "title": "CHINA – X-RAY EQUIPMENT", "complainant": "European Union", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4, 3.5, 6.5.1,\n6.9"], "articles": [], "subject": "Anti-dumping duties imposed by China’s Ministry of Commerce (MOFCOM) by Notice No. 1 (2011),", "sector": "Anti-Dumping", "year": 2013, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2013", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 (injury determination) and 3.2 (injury determination – volume of imports): The Panel held that MOFCOM’s price undercutting and price suppression analyses were inconsistent with Arts. 3.1 and 3.2. The Panel found that the price effects analysis were not based on an objective examination of positive evidence, as MOFCOM had failed to ensure that the prices it was comparing as part of its price effects analysis were comparable. • ADA Arts. 3.1 (injury determination) and 3.4 ((injury determination – injury factors): The Panel found MOFCOM acted inconsistently with Arts. 3.1 and 3.4 ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS427", "title": "CHINA – BROILER PRODUCTS", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 2.2.1.1, 3.1, 3.2, 3.4, 3.5,\n4", "ASCM Arts. 12.4.1, 12.7,\n12.8, 15.1, 15.", "GATT Art. VI"], "articles": [], "subject": "Imposition of anti-dumping and countervailing measures by China.", "sector": "Subsidies & Anti-Subsidy", "year": 2013, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2013", "summary_ar": "", "summary_en": "• ADA Art. 6.2 (defence of parties' interests): The Panel found that China’s Ministry of Commerce (MOFCOM) had failed to provide an opportunity for interested parties with adverse interests to meet and present their views, in violation of Art. 6.2. • ADA Art. 6.5.1 and ASCM Art. 12.4.1 (provision of non-confidential summaries): The Panel found that the nonconfidential summaries of the information redacted from the confidential version of the Petition did not provide a reasonable understanding of the information submitted in confidence. • ADA Art. 6.9 and ASCM Art. 12.8 (disclosure of essential", "keywords": ["subsidies & anti-subsidy", "ADA", "ASCM", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS429", "title": "US – SHRIMP II (VIET NAM)", "complainant": "United States", "respondent": "Viet Nam", "third_parties": [], "agreements": ["GATT Art. VI", "ADA Arts. 1, 6, 9, 11 and 18.1, Annex\nII", "DSU Arts. 4, 6, 7, and 11"], "articles": [], "subject": "Certain United States' laws, methodologies and practices with respect to the imposition, assessment", "sector": "Agriculture & Food", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2015", "summary_ar": "", "summary_en": "• ADA Art. 9.3 and GATT Art. VI: 2 (imposition and collection of anti‑dumping duties): Although the Panel found that Viet Nam had failed to establish that the simple zeroing methodology used in United States' administrative reviews is a measure of general and prospective application that can be challenged as such, the Panel found that the United States acted inconsistently with ADA Art. 9.3 and GATT Art. VI:2 by applying the simple zeroing methodology to calculate the dumping margins of the respondents in the fourth, fifth, and sixth administrative reviews under the shrimp anti‑dumping order. ", "keywords": ["agriculture & food", "GATT", "ADA", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS430", "title": "INDIA – AGRICULTURAL PRODUCTS", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["GATT", "SPS"], "articles": [], "subject": "Import prohibitions imposed on imports of certain agricultural products due to concerns relating to ", "sector": "Agriculture & Food", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2015", "summary_ar": "", "summary_en": "• SPS Arts. 3.1 and 3.2 (harmonization with international standards): The Appellate Body upheld the Panel's findings that India's AI measures were inconsistent with Art. 3.1 because they were not based on an international standard (Chapter 10.4 of OIE3 Terrestrial Code), and that India was not entitled to benefit from the presumption of consistency of its AI measures with the SPS Agreement and the GATT 1994 (Art. 3.2). The Appellate Body also found that the Panel did not act inconsistently with SPS Article 11.2 or DSU Art. 13.2 in consulting with the OIE regarding the meaning of the Terrestria", "keywords": ["agriculture & food", "GATT", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS431", "title": "CHINA – RARE EARTHS", "complainant": "United States, European Union, Japan", "respondent": "China", "third_parties": [], "agreements": ["GATT\nArts. XI and XX"], "articles": [], "subject": "Export restrictions on a number of rare earths, tungsten, and molybdenum. The export restrictions", "sector": "Other", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2014", "summary_ar": "", "summary_en": "• Accession Protocol (export duties)/Marrakesh Agreement/GATT Art. XX (general exceptions): The Panel found that China's export duties on rare earths, tungsten, and molybdenum were inconsistent with its Accession Protocol. In its examination of this issue and China's defence under Art. XX, the Panel was mindful of the Appellate Body ruling that absent “cogent reasons an adjudicatory body will resolve the same legal question in the same way in a subsequent case”. The Panel concluded that none of China's arguments constituted cogent reasons for departing from the Appellate Body's finding in Chin", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS436", "title": "US – CARBON STEEL (INDIA)", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1"], "articles": [], "subject": "Imposition by the United States of countervailing duties on imports of certain hot-rolled carbon ste", "sector": "Metals & Mining", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2014", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Appellate Body reversed the Panel’s finding rejecting India’s claim that the United States Department of Commerce (USDOC) determination that the National Mineral Development Corporation (NMDC) was a public body was inconsistent with ASCM Art. 1.1(a)(1). The Appellate Body considered that the Panel had correctly articulated the appropriate standard but had erred in its substantive interpretation of ASCM Art. 1.1(a)(1) by construing the term “public body” to mean any entity that is “meaningfully controlled” by a government. Consequently, t", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS437", "title": "US – COUNTERVAILING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI\nSCM Arts. 1.1, 1.1", "SCM Arts. 1.1, 1.1"], "articles": [], "subject": "Countervailing measures imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2015", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Panel found that the United States Department of Commerce (USDOC) acted inconsistently with Art. 1.1(a)(1), because it determined that certain Chinese state-owned enterprises were “public bodies” based solely on the grounds that they were majority owned, or otherwise controlled, by the Government of China. The Panel also found USDOC's “rebuttable presumption” to determine whether a state-owned enterprise is a “public body” to be inconsistent as such with Art. 1.1(a)(1). • ASCM Arts. 1.1(b) and 14(d) (benefit benchmark): The Panel found t", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS438", "title": "ARGENTINA – IMPORT MEASURES", "complainant": "United States, Japan", "respondent": "European Union", "third_parties": [], "agreements": ["GATT Arts. III"], "articles": [], "subject": "Other", "sector": "Other", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2015", "summary_ar": "", "summary_en": "• The Appellate Body upheld the Panel's finding that the Argentine authorities' imposition on economic operators of one or more five trade-related requirements (TRRs), as a condition to import or to obtain certain benefits, operated as a single measure attributable to Argentina (a TRRs measure). • DSU Art. 6.2 (requirements of panel request): The Appellate Body reversed the Panel's finding that 23 specific instances of application of the TRRs were not properly identified in the European Union's panel request as measures at issue and were not within the Panel's terms of reference. However, the ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS440", "title": "CHINA – AUTOS (US)", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "Anti-dumping and countervailing duties imposed by China on certain automobiles from the United State", "sector": "Subsidies & Anti-Subsidy", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2014", "summary_ar": "", "summary_en": "• ADA Art. 6.5.1/ASCM Art. 12.4.1 (evidence – confidential information): The Panel found a violation of these two provisions on the ground that MOFCOM had failed to require the petitioner to furnish adequate non-confidential summaries of confidential information presented in the petition. • ADA Art. 6.9 (evidence – essential facts): The Panel found a violation of this provision on the ground that MOFCOM had failed to disclose essential facts to US company respondents, specifically the data and calculations underlying their respective dumping margins. • ADA Art. 6.8 and Annex II para. 1/ASCM Ar", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS442", "title": "EU – FATTY ALCOHOLS (INDONESIA)", "complainant": "Indonesia", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 1, 2.3, 2.4, 2.6, 3.1, 3.2, 3.", "GATT 1994 Arts. VI and X"], "articles": [], "subject": "Anti-dumping duties imposed by the European Union on imports of fatty alcohols from Indonesia, and", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (fair comparison): The EU authorities made a downward adjustment to the export price of an Indonesian producer (PT Musim Mas) for payment made by PT Musim Mas to a related trading company based in Singapore (ICOF‑S). Indonesia claimed that PT Musim Mas and ICOF‑S formed a “single economic entity” and therefore, the payment (mark-up) was not a difference affecting price comparability within the meaning of Art. 2.4. The Appellate Body observed that the focus of Art. 2.4 is not merely on a comparison between the normal value and the export price, but predominantly on the means to e", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS447", "title": "US – ANIMALS", "complainant": "Argentina", "respondent": "United States", "third_parties": [], "agreements": ["SPS Arts. 1.1, 2.2, 2.3, 3.1, 3.3,\n5.1, "], "articles": [], "subject": "(i) the import prohibition of fresh (chilled or frozen) beef from Argentina; (ii) the failure to rec", "sector": "Agriculture & Food", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2015", "summary_ar": "", "summary_en": "• SPS Art. 3.1 (harmonization with international standards): The Panel agreed with the United States that “based on” did not require wholesale adoption of the international standard into the measure by the importing Member. However, the Panel held that a Member's measure could not contradict the international standard, and nevertheless be considered based on it within the meaning of Art. 3.1. As the United States' measures contradicted certain key elements of the OIE2 Terrestrial Animal Health Code, the relevant international standard, the Panel found that the United States' measures were inco", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS449", "title": "US – COUNTERVAILING AND ANTI-DUMPING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. X", "SCM Arts. 10"], "articles": [], "subject": "Subsidies & Anti-Subsidy", "sector": "Subsidies & Anti-Subsidy", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2014", "summary_ar": "", "summary_en": "• GATT Art. X:1 (trade regulations – prompt publication): In a finding not appealed, the Panel found that Section 1 of PL112‑99 was published promptly after it had been made effective because it was published on the same date that it was made effective, and thus the United States did not act inconsistently with Art. X:1 in respect of Section 1. • GATT Art. X:2 (trade regulations – no enforcement before publication): The Appellate Body reversed the Panel's finding that, although Section 1 of PL 112‑99 is a measure of general application that has been “enforced” prior to its official publication", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS453", "title": "ARGENTINA – FINANCIAL SERVICES", "complainant": "Argentina", "respondent": "Panama", "third_parties": [], "agreements": ["GATT", "GATS"], "articles": [], "subject": "Services", "sector": "Services", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2016", "summary_ar": "", "summary_en": "• GATS Arts. II:1 and XVII:1 (likeness): The Appellate Body considered that, in the absence of a finding that measures 1-8 provided for a distinction based exclusively on origin, and by failing to conduct an analysis of “likeness” on the basis of the arguments and evidence presented by Panama, the Panel had erred in finding “likeness” “by reason of origin”. On this basis, the Appellate Body reversed the Panel’s finding of likeness of the services and service suppliers at issue under Arts. II:1 and XVII:1.2 • GATS Arts. II:1 and XVII:1 (less favourable treatment): The Appellate Body found that,", "keywords": ["services", "GATT", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS456", "title": "INDIA – SOLAR CELLS", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Domestic content requirements (DCR measures) imposed by India in the initial phases of India's Jawah", "sector": "Energy & Environment", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Energy & Environment السعودي — تستحق المتابعة", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. III:4 and TRIMS Art 2.1 (national treatment): The Appellate Body upheld the Panel's finding that India's DCR measures were inconsistent with WTO non‑discrimination obligations under Art. III:4 and Art. 2.1. • GATT Art. III:8(a) (government procurement derogation): The Appellate Body concluded that the Panel was properly guided by its report in Canada – Renewable Energy in finding that the measures were not covered by the derogation under Art. III:8(a) because the product being procured (electricity) was not in a “competitive relationship” with the product discriminated against (sol", "keywords": ["energy & environment", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS457", "title": "PERU – AGRICULTURAL PRODUCTS", "complainant": "Peru", "respondent": "Guatemala", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Peru's Price Range System (PRS), which resulted in the imposition of an additional duty, when the", "sector": "Agriculture & Food", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2015", "summary_ar": "", "summary_en": "• AA Art. 4.2, footnote 1 (market access): The Appellate Body upheld the Panel's finding that the additional duties resulting from the PRS constituted variable import levies, or at least a border measure similar to variable import levies, within the meaning of footnote 1 of the AA, and that, by maintaining such a measure, Peru had acted inconsistently with Art. 4.2. • GATT Art. II:1(b) (schedules of concessions): The Appellate Body upheld the Panel's finding that the additional duties resulting from the PRS constituted other duties or charges imposed on or in connection with the importation, w", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS461", "title": "COLOMBIA – TEXTILES", "complainant": "Panama", "respondent": "Colombia", "third_parties": [], "agreements": ["GATT Arts. II"], "articles": [], "subject": "A compound tariff imposed by Colombia through Presidential Decree No. 074/2013, on imports of", "sector": "Textiles", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body reversed the Panel's finding that it was unnecessary for the Panel to rule on whether Art. II:1 applies to “illicit trade”. The Appellate Body considered that the basis upon which the Panel had refrained from interpreting Art. II:1 was flawed. According to the Appellate Body, the Panel's statement implied that the measure at issue applied, or could apply, to some transactions considered by Colombia to be illicit trade, and thus the Panel was required to address the interpretative issue before it. The Appellate Body therefore found", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS464", "title": "US – WASHING MACHINES", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2.4.2, 2.4, 9.3\nGATT Arts. VI", "GATT Arts. VI"], "articles": [], "subject": "Definitive anti-dumping and countervailing duties applied by the US Department of Commerce (USDOC).", "sector": "Subsidies & Anti-Subsidy", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2, second sentence (pattern): The Appellate Body considered that a “pattern” comprises all export prices to a purchaser (or region or time period) which differ significantly from the export prices to other purchasers (or regions or time periods) because they are significantly lower than those other prices. The Appellate Body also found that the requirement to identify prices which differ significantly means that the authority is required to assess the price differences in a quantitative and qualitative manner. The Appellate Body thus reversed the Panel's findings to the extent i", "keywords": ["subsidies & anti-subsidy", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS468", "title": "UKRAINE – PASSENGER CARS", "complainant": "Japan", "respondent": "Ukraine", "third_parties": [], "agreements": ["SA Arts. 2.1, 3.1, 4.1", "GATT Arts. II"], "articles": [], "subject": "The definitive safeguard measure imposed by Ukraine in April 2013 for three years on products at iss", "sector": "Safeguards", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2015", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a)(unforeseen developments and the effect of GATT obligations): The Panel found that Ukraine acted inconsistently with this provision because the Ukrainian competent authorities did not provide in their published report a demonstration of the circumstances – unforeseen developments and the effect of GATT obligations – that must be satisfied before a safeguard measure can be imposed. • SA Art. 2.1 (conditions for safeguard measures – increased imports): The Panel found that Ukraine did not adequately analyse and explain the intervening trends and failed to demonstrate that the", "keywords": ["safeguards", "SA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS471", "title": "US – ANTI-DUMPING METHODOLOGIES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2.4.2, 6.1, 6.8, 6.10, 9.2,\n9.", "GATT Art. VI"], "articles": [], "subject": "Measures relating to certain United States’ anti-dumping investigations against imports from China: ", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (W-T methodology): The Panel found that the United States acted inconsistently in two of the three antidumping investigations by disregarding non-target prices that were lower than the alleged target price under the price gap test, and by failing to consider evidence on all non-target prices making up the weighted average non-target price gap. The Panel also found that the United States acted inconsistently in the three investigations by applying the W-T methodology to all export transactions, and using zeroing in the dumping margin calculations, as well as by premising the ex", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS473", "title": "EU – BIODIESEL (ARGENTINA)", "complainant": "غير محدد", "respondent": "European Union", "third_parties": [], "agreements": ["GATT", "ADA"], "articles": [], "subject": "Anti-Dumping", "sector": "Anti-Dumping", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Arts. 2.2.1.1 and 2.2 / GATT Art. VI:1(b)(ii) / DSU Art. 11 (as such claims): The Appellate Body upheld the Panel’s finding that Argentina had not established that the second subparagraph of Art. 2(5) of the Basic Regulation was inconsistent as such with Arts. 2.2.1.1, 2.2 and VI:1(b)(ii). • ADA Art. 2.2.1.1 (dumping determination – cost of production on the basis of records kept): The Appellate Body considered that the second condition in the first sentence of Art. 2.2.1.1 concerns whether the records kept by the investigated exporter/producer suitably and sufficiently correspond to or ", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS475", "title": "RUSSIA – PIGS (EU)", "complainant": "European Union", "respondent": "Russia", "third_parties": [], "agreements": ["SPS Arts. 1, 2.2, 2.3, 3.1, 3.2, 5.1,\n5."], "articles": [], "subject": "Agriculture & Food", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2017", "summary_ar": "", "summary_en": "• SPS Art. 3 (harmonization): The Panel found that the EU member State bans violated Art. 3.2 because they did not conform to the relevant OIE international standards. It found that the EU-wide ban and EU member State bans, except that in respect of Latvia, were inconsistent with Art. 3.1 because they were not based on the same standards. • SPS Arts. 5.1, 5.2, 5.3 and 2.2 (risk assessment): The Panel found that (i) the measures were not provisional measures under Art. 5.7, (ii) they violated Arts. 5.1 and 5.2 because they were not based on a risk assessment within the meaning of the Agreement,", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS477", "title": "INDONESIA – IMPORT LICENSING REGIMES", "complainant": "United States, Indonesia", "respondent": "New Zealand", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "These two disputes concerned 18 measures imposed by Indonesia on the importation of horticultural", "sector": "Other", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2017", "summary_ar": "", "summary_en": "• Order of analysis: AA Art. 4.2 (market access)/GATT Art. XI:1 (quantitative restrictions): The Appellate Body held that Art. 4.2 does not apply to the exclusion of Art. XI:1. Rather, both provisions contain the same substantive obligations in relation to the claims at issue and therefore apply cumulatively. The Appellate Body also found that there is no mandatory sequence of analysis between these two provisions and therefore upheld the Panel’s decision to begin with Art. XI:1. • Burden of proof: GATT Art. XX (general exceptions)/AA Art. 4.2 footnote 1: The Appellate Body upheld the Panel’s ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS479", "title": "RUSSIA – COMMERCIAL VEHICLES", "complainant": "European Union", "respondent": "Russia", "third_parties": [], "agreements": ["ADA Arts. 1, 3.1, 3.2, 3.4, 3.5, 4.1,\n6.", "GATT Art. VI"], "articles": [], "subject": "The Russian Federation’s imposition of anti-dumping duties on certain light commercial vehicles from", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 4.1 (definition of domestic industry): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 4.1 by not including GAZ, a domestic producer of the like product, in its definition of “domestic industry” solely on the basis that it had furnished allegedly deficient data. • ADA Arts. 3.1 and 3.2 (price suppression): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 3.2 by failing to take into account the impact of the financial crisis in determining the rate of return used to constru", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS480", "title": "EU – BIODIESEL (INDONESIA)", "complainant": "Indonesia", "respondent": "European Union", "third_parties": [], "agreements": ["GATT", "ADA"], "articles": [], "subject": "Anti-dumping measures imposed by the European Union on imports of biodiesel from Indonesia.", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Arts. 2.2 and 2.2.1.1/GATT Art. VI:1(b)(ii) (cost of production): The Panel upheld Indonesia’s claim that the European Union acted inconsistently with Art. 2.2.1.1 by failing to calculate the cost of production of the producers under investigation on the basis of the records kept by the producers. In addition, the Panel upheld Indonesia’s separate claims that the European Union acted inconsistently with Art. 2.2 of the and Art. VI:1(b)(ii) by using a “cost” that was not the cost prevailing “in the country of origin” in the construction of the normal value. The Panel did not make findings", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS482", "title": "CANADA – WELDED PIPE", "complainant": "Taipei", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Art. VI, ADA Arts. 1, 3.1, 3.2,\n3.4", "ADA Arts. 1, 3.1, 3.2,\n3.4, 3.5, 3.7, 5."], "articles": [], "subject": "Anti-Dumping", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Arts. 5.8 and 9.2 (termination of investigation and imposition of anti-dumping duties)(treatment of de minimis exporters): The Panel found that (i) Canada’s failure to immediately terminate the investigation of exporters with final de minimis dumping margins, and (ii) the underlying legislation, “as such”, which did not provide discretion to immediately terminate such investigations, violated the second sentence of Art. 5.8 because immediate termination is triggered by individual producers/exporters’ dumping margins, rather than country-wide margins. The Panel hence also considered that ", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS483", "title": "CHINA – CELLULOSE PULP", "complainant": "Canada", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4 and 3.5"], "articles": [], "subject": "Anti-Dumping", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.2 (injury determination – volume of dumped imports): The Panel found that China did not act inconsistently with Arts. 3.1 and 3.2 in not assessing the significance of an absolute increase in dumped imports in light of the factual circumstances in the market such as domestic demand, volume of domestic like product and non-dumped imports. The Panel highlighted the separate nature of the inquiries set out in Art. 3.2 and considered that while the principle in Art. 3.1 that an injury determination must be based on an objective examination of positive evidence applies generall", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS484", "title": "INDONESIA – CHICKEN", "complainant": "Indonesia", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT", "SPS"], "articles": [], "subject": "(i) alleged (unwritten) general prohibition resulting from the combined operation of several differe", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2017", "summary_ar": "", "summary_en": "General prohibition • While the Panel established that the measure was properly identified and therefore within its terms of reference, it found that Brazil had not demonstrated the existence of alleged (unwritten) general prohibition. Measure 1: Positive list requirement • The Panel found that the positive list requirement in its version at panel establishment resulted in a ban that was inconsistent with GATT Art. XI. It further found that the ban was not justified under GATT Art. XX as it did not meet the necessity requirement under Art. XX(d). • The Panel found that subsequent amendments ha", "keywords": ["agriculture & food", "GATT", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS485", "title": "RUSSIA – TARIFF TREATMENT", "complainant": "European Union", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Arts. II"], "articles": [], "subject": "Other", "sector": "Other", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1(b) (schedules of concessions): The Panel found that a measure can be found to be inconsistent with Art. II:1(b), first sentence, on the basis of its design and structure, and that it is not necessary to provide evidence of actual transactions or adverse trade effects. The Panel also found that Art. II:1(b), first sentence, prohibits Members from exceeding their tariff bindings by even de minimis amounts. Finally, the Panel confirmed that Members cannot balance less favourable tariff treatment of some imports against more favourable treatment of others. Thus, a Member may not i", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS486", "title": "EU – PET (PAKISTAN)", "complainant": "Pakistan", "respondent": "European Union", "third_parties": [], "agreements": ["GATT", "SCM"], "articles": [], "subject": "Subsidies & Anti-Subsidy", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• DSU Arts. 3 and 11 (expiry of the measure at issue): The Appellate Body found that the Panel made an objective assessment that “the matter” before it still required to be examined because the parties were still in disagreement as to the “applicability of and conformity with the relevant covered agreements” in respect of the European Commission’s (the Commission) findings underpinning the expired measure at issue. Accordingly, The Appellate Body found that the European Union did not demonstrate that the Panel failed to comply with Art. 11 of the DSU when it decided to make findings on Pakista", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS487", "title": "US – TAX INCENTIVES", "complainant": "European Union", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1"], "articles": [], "subject": "Legislation enacted in the state of Washington in the United States that amended and extended tax", "sector": "Subsidies & Anti-Subsidy", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2017", "summary_ar": "", "summary_en": "• ASCM Art. 1 (definition of a subsidy): The Panel found that the tax rate, credit or exemption at issue for each of the challenged measures constituted a financial contribution under Art. 1.1(a)(1)(ii) because (i) government revenue that is otherwise due is foregone or not collected, and (ii) a benefit within the meaning of Art. 1.1(b) is thereby conferred. It thus concluded that each of the measures constituted a subsidy under Art. 1. • ASCM Art. 3 (prohibited subsidies – import substitution subsidies): The Appellate Body upheld the Panel’s finding that the siting provisions challenged by th", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS488", "title": "US – OCTG (KOREA)", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["GATT", "ADA"], "articles": [], "subject": "Anti-Dumping", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Art. 2.2 (dumping determination – “viability test” for use of third-country export sales): The Panel concluded that Art. 2.2 does not impose any limitation on the criteria that a Member may establish to decide which of the alternative methods contained therein to use. Consequently, the United States’ viability test is not “as such” inconsistent with Art. 2.2. The Panel also stated that Art. 2.2 does not impose any obligation on a Member to examine whether a respondent’s third-country export prices are representative if it has opted to use constructed normal value to determine normal valu", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS490", "title": "INDONESIA – IRON OR STEEL PRODUCTS", "complainant": "Indonesia", "respondent": "Taipei", "third_parties": [], "agreements": ["GATT Arts. I", "SA Arts. 2.1, 3.1, 4.1, 4.2"], "articles": [], "subject": "A specific duty applied by Indonesia on imports of galvalume", "sector": "Metals & Mining", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• SA and GATT Art. XIX (the specific duty as a safeguard measure): Although both sides maintained that the measure at issue was a safeguard measure, the Panel found that, in discharging its duty to undertake “an objective assessment of the matter”, it should examine the issue itself. The Panel observed that Indonesia did not have a tariff binding on galvalume, and concluded that the measure was not a safeguard within the meaning of SA Art. 1, insofar as it did not suspend, withdraw or modify a relevant GATT obligation or concession for purposes of remedying or preventing serious injury. The Ap", "keywords": ["metals & mining", "GATT", "SA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS491", "title": "US – COATED PAPER (INDONESIA)", "complainant": "Indonesia", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 3.5, 3.7, 3.8", "ASCM Arts. 2.1"], "articles": [], "subject": "(1) The US International Trade Commission’s (USITC) and the Department of Commerce’s (UDSOC)", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Art. 14(d) (rejection of in-country prices as benchmarks): The Panel rejected Indonesia’s argument that the USDOC improperly concluded that Indonesian prices for standing timber and logs were unusable as benchmarks. The UDSOC did not based its decision solely on the majority public ownership of land for timber. Prices of timber harvested from private land could be disregarded because the provided data was not representative. The USDOC was not required to seek further data from other sources, e.g. private companies. No log prices were unaffected by the export ban on logs and therefore us", "keywords": ["subsidies & anti-subsidy", "ADA", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS492", "title": "EU – POULTRY MEAT (CHINA)", "complainant": "China", "respondent": "European Union", "third_parties": [], "agreements": ["GATT Arts. I"], "articles": [], "subject": "The modification by the European Union of tariff concessions on certain poultry products pursuant to", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2017", "summary_ar": "", "summary_en": "• GATT Art. XXVIII (modification of schedules): The Panel found that the European Union had not acted inconsistently with Art. XXVIII:1 by not recognizing China as a Member holding a principal or substantial supplying interest in the concessions at issue because (i) it was not obliged to take into account the SPS measures that restricted Chinese poultry imports over the relevant reference periods since they were not “discriminatory quantitative restrictions”; and (ii) it was not obliged to re-determine which Members held a substantial supplying interest based on changes in import shares after ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS493", "title": "UKRAINE – AMMONIUM NITRATE", "complainant": "Russia", "respondent": "Ukraine", "third_parties": [], "agreements": ["ADA Arts. 1, 2.1, 2.2, 2.2.1, 2.2.1.1,\n2", "GATT 1994 Art. VI\nDSU Arts. 6.2, 7.1, 11", "DSU Arts. 6.2, 7.1, 11"], "articles": [], "subject": "Anti-Dumping", "sector": "Anti-Dumping", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2019", "summary_ar": "", "summary_en": "• DSU Art. 6.2 (identification of measures): In a finding upheld by the Appellate Body, the Panel found that the references in Russia’s panel request to the decisions in the original investigation phase (the 2008 amended decision and 2010 amendment) were “sufficiently precise” to identify the specific measures at issue and fell within its terms of reference. • DSU Arts. 7.1, 11 (mandate, objective assessment): Accordingly, the Appellate Body concluded that the Panel did not err under DSU Arts. 7.1 and 11 by ruling on Russia’s ADA Art. 5.8 claim as it relates to the 2008 amended decision the 20", "keywords": ["anti-dumping", "ADA", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS495", "title": "KOREA – RADIONUCLIDES", "complainant": "Japan", "respondent": "Korea", "third_parties": [], "agreements": ["SPS Arts. 2.3, 5.6, 5.7, 7, and 8,\nAnnex"], "articles": [], "subject": "Agriculture & Food", "sector": "Agriculture & Food", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2019", "summary_ar": "", "summary_en": "• SPS Art. 5.6 (appropriate level of protection): The Panel identified Korea’s ALOP as consisting of both qualitative aspects and a quantitative element of radiation dose limit. The Appellate Body reversed the Panel’s findings of inconsistency with Art. 5.6 based on the Panel’s failure to then consider all elements of the identified ALOP. The Appellate Body found that the Panel erred by focusing on the quantitative element as a decisive indicator of whether Japan’s proposed alternative measure would achieve Korea’s ALOP, contrary to its articulation of the ALOP as containing multiple elements.", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS499", "title": "RUSSIA – RAILWAY EQUIPMENT", "complainant": "غير محدد", "respondent": "AGREEMENT", "third_parties": [], "agreements": ["GATT", "TBT"], "articles": [], "subject": "Standards & TBT", "sector": "Standards & TBT", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2020", "summary_ar": "", "summary_en": "• TBT Art. 5.1.1 (conformity assessment procedures – comparable situation): The Panel found that, in respect of the instructions suspending certificates and the decisions rejecting applications for certificates, Ukraine failed to establish that Russia had acted inconsistently with Art. 5.1.1. The Appellate Body considered that, in examining factors relevant for establishing the existence of a “comparable situation”, the Panel did not focus sufficiently on aspects specific to the suppliers who were claimed to have been granted access under less favourable conditions or to their location. The Ap", "keywords": ["standards & tbt", "GATT", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS504", "title": "KOREA – PNEUMATIC VALVES (JAPAN)", "complainant": "Japan", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 1, 3.1, 3.2, 3.4, 3.5, 4.1,\n6.", "GATT 1994 Art. VI"], "articles": [], "subject": "Definitive anti-dumping duties imposed by Korea on imports of pneumatic valves originating from Japa", "sector": "Anti-Dumping", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2019", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.4 (injury determination – magnitude of the margin of dumping): The Appellate Body agreed with the Panel that Art. 3.4 does not require that any of the factors listed in Art. 3.4 be evaluated “in a particular manner” or given “a particular relevance or weight”, and upheld the Panel’s finding that the Korean investigating authorities’ evaluation of the magnitude of the margin of dumping was not inconsistent with Arts. 3.1 and 3.4. • ADA Arts. 3.1 and 3.5 (injury determination – causation): First, the Panel found that the Korean investigating authorities did not violate Arts", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS505", "title": "US – SUPERCALENDERED PAPER", "complainant": "United States, Canada", "respondent": "2.", "third_parties": [], "agreements": ["ASCM Art. 1.1", "GATT Art. VI"], "articles": [], "subject": "Certain countervailing measures with respect to supercalendered paper from Canada; and the United St", "sector": "Subsidies & Anti-Subsidy", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2020", "summary_ar": "", "summary_en": "", "keywords": ["subsidies & anti-subsidy", "ASCM", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS511", "title": "CHINA – AGRICULTURAL PRODUCERS", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["AA Arts. 3.2, 6.3 and 7.2"], "articles": [], "subject": "China’s provision for domestic support, in the form of market price support, in excess of its produc", "sector": "Agriculture & Food", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2019", "summary_ar": "", "summary_en": "• AA Arts. 3.2 and 6.3 (domestic support commitments): The Panel found that China provided domestic support, in terms of its Current Total Aggregate Measurement(s) of Support (AMS), in the form of market price support to the producers of certain agricultural products in excess of its commitment level of “nil”, set forth in Section I of Part IV of China’s Schedule of Concessions on Goods CLII, in violation of Arts. 3.2 and 6.3. • AA Art. 7.2(b) (prohibition of domestic support to agricultural producers in excess of the relevant de minimis level): Having found that China had acted inconsistently", "keywords": ["agriculture & food", "AA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS512", "title": "RUSSIA – TRAFFIC IN TRANSIT", "complainant": "Ukraine", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Art. XX1"], "articles": [], "subject": "Other", "sector": "Other", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2019", "summary_ar": "", "summary_en": "• GATT 1994 Art. XXI(b)(iii) (national security exception not totally self-judging – measures taken in an emergency in international relations): The Panel interpreted Art. XXI(b) as vesting in panels the power to review whether the requirements of the enumerated subparagraphs were met, rather than leaving it to the unfettered discretion of the invoking Member. Accordingly, the Panel rejected the Russian Federation’s argument that the Panel lacked jurisdiction to review the Russian Federation’s invocation of Art. XXI(b)(iii). The Panel considered that an “emergency in international relations” r", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS513", "title": "MOROCCO – HOT-ROLLED STEEL (TURKEY)", "complainant": "Turkey", "respondent": "Morocco", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.4, 5.10, 6.8, 6.9"], "articles": [], "subject": "Definitive anti-dumping measures imposed by Morocco on imports from, among others, Turkey.", "sector": "Metals & Mining", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 5.10 (time-limit for conclusion of investigation): The Panel found that Morocco had acted inconsistently with Art. 5.10 by failing to conclude the investigation within the 18-month maximum time limit set out in that provision. • ADA Art. 3.1 (injury determination – establishment of domestic industry): The Panel found that Morocco had acted inconsistently with Art.3.1 in determining that the domestic industry was “unestablished”. • ADA Arts. 3.1 and 3.4 (injury determination): The Panel found that Morocco had acted inconsistently with Arts. 3.1 and 3.4 by improperly conducting the in", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS517", "title": "CHINA – TRQS", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATT 1994, Arts. X"], "articles": [], "subject": "Administration of tariff rate quotas (TRQs) for wheat, short- and medium- grain rice, long grain ric", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2017", "summary_ar": "", "summary_en": "• Para. 116 of China’s Working Party Report (through para. 1.2 of China’s Accession Protocol): This was the first dispute to address para. 116. Considering the requirements set forth in para. 116, as applicable to China’s administration of its TRQs, the Panel found that: (i) the basic eligibility criteria (considering also the practice of assessment using Credit China’s blacklist of entities) were inconsistent with the obligations to administer TRQs on a transparent, predictable, and fair basis, and using clearly specified requirements; (ii) the allocation principles were inconsistent with the", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS524", "title": "COSTA RICA – AVOCADOS (MEXICO)", "complainant": "Costa Rica", "respondent": "Mexico", "third_parties": [], "agreements": ["SPS Arts. 1.1, 2.1, 2.2, 2.3, 3.1, 3.3,\n", "GATT Arts. III"], "articles": [], "subject": "Measures on the importation of fresh avocados from Mexico, related to Avocado sunblotch viroid (ASBV", "sector": "Agriculture & Food", "year": 2022, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود على المصالح التجارية السعودية المباشرة", "request_date": "2022", "summary_ar": "", "summary_en": "• SPS Arts. 5.1, 5.2, and 5.3 (risk assessment), and Art. 2.2 (scientific principles and sufficient scientific evidence): The Panel analysed the risk assessment in Costa Rica’s PRA reports, including Costa Rica’s determination of freedom from ASBVd, the methodology in the manual, the cross-cutting themes of diversion from intended use and spontaneous germination, and the SFE’s analysis of factors that led it to conclude that there was a high risk of entry, establishment, and spread of ASBVd. The Panel found that Costa Rica violated: (i) Arts. 5.1, 5.2, and 5.3, by failing to ensure that its ph", "keywords": ["agriculture & food", "SPS", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS529", "title": "AUSTRALIA – ANTI-DUMPING MEASURES ON PAPER", "complainant": "Indonesia", "respondent": "Australia", "third_parties": [], "agreements": ["ADA Arts. 2.2, 2.2.1.1, 9.3"], "articles": [], "subject": "Anti-dumping measure imposed on imports from Indonesia following an anti-dumping investigation by th", "sector": "Anti-Dumping", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي — تستحق المتابعة", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 2.2: (dumping determination – particular market situation): Prior to this Panel, no panel or AB report had interpreted the phrase “particular market situation” as it appears in Art. 2.2, which provides for the discarding of domestic sales as the basis for normal value when “because of a particular market situation … such sales do not permit a proper comparison”. 2 The Panel found that a “particular market situation” is only relevant insofar as it has the effect of rendering domestic sales unfit to permit a proper comparison, and further found that the phrase does not lend itself to ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS546", "title": "UNITED STATES – SAFEGUARD MEASURE ON IMPORTS OF", "complainant": "United States", "respondent": "Korea", "third_parties": [], "agreements": ["SA", "GATT 1994"], "articles": [], "subject": "Safeguards", "sector": "Safeguards", "year": 2023, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي — تستحق المتابعة", "request_date": "2023", "summary_ar": "", "summary_en": "Korea raised several claims under the Safeguards Agreement and the GATT 1994 challenging (a) different aspects of the USITC's determination, (b) the nature and level of the safeguard measure imposed by the United States based on that determination, and specifically whether it went beyond what was necessary to remedy the serious injury to the domestic industry and (c)the United States' alleged violation of obligations undertaken in connection with the conduct of a safeguard investigation. Key Findings are as follows: • SA Arts 4.1 and 3.1 (definition of the domestic industry): The Panel upheld ", "keywords": ["safeguards", "SA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS577", "title": "US — RIPE OLIVES FROM SPAIN", "complainant": "United States", "respondent": "European Union", "third_parties": [], "agreements": ["GATT", "SCM", "ADA"], "articles": [], "subject": "Subsidies & Anti-Subsidy", "sector": "Subsidies & Anti-Subsidy", "year": 2021, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي — تستحق المتابعة", "request_date": "2021", "summary_ar": "", "summary_en": "• Specificity: The Panel upheld several claims raised by the European Union concerning the United States' findings of de jure specificity in the countervailing duty investigation. The USDOC had determined that the eligibility criteria for subsidies conferred to raw olive growers under the current EU Common Agricultural Policy was legally tied to the subsidy amounts provided exclusively to raw olive growers under predecessor programmes, and therefore that it retained and continued the inherent de jure specificity of those earlier, expired programmes. The Panel found that the USDOC had erred in ", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS595", "title": "EU – SAFEGUARD MEASURES ON STEEL (TURKEY)", "complainant": "Turkey", "respondent": "European Union", "third_parties": [], "agreements": ["GATT"], "articles": [], "subject": "Provisional and definitive safeguards on imports of certain steel products, taking the form of tarif", "sector": "Metals & Mining", "year": 2022, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي — تستحق المتابعة", "request_date": "2022", "summary_ar": "", "summary_en": "", "keywords": ["metals & mining", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}]


# ══════════════════════════════════════════════════════════════════════════════
# COMBINED DATASET: Merge both sources, deduplicate by DS number
# ══════════════════════════════════════════════════════════════════════════════
def build_combined_dataset():
    combined = {}
    # PDF data first (base layer)
    for d in WTO_PDF_DISPUTES:
        combined[d['ds_number']] = d
    # Saudi curated cases override/supplement (higher quality metadata)
    for d in WTO_SAUDI_CASES:
        combined[d['ds_number']] = d
    return list(combined.values())

WTO_ALL_DISPUTES = build_combined_dataset()

# ─── Stats ────────────────────────────────────────────────────────────────────
def build_stats():
    disputes = WTO_ALL_DISPUTES
    stats = {
        "total": len(disputes),
        "total_pdf": len(WTO_PDF_DISPUTES),
        "total_saudi_curated": len(WTO_SAUDI_CASES),
        "by_year": {},
        "by_sector": {},
        "by_status": {},
        "by_agreement": {},
        "saudi_involvement": {"direct": 0, "third_party": 0, "high_relevance": 0, "medium_relevance": 0},
        "top_complainants": {},
        "top_respondents": {}
    }
    for d in disputes:
        y = str(d.get("year",""))
        if y: stats["by_year"][y] = stats["by_year"].get(y, 0) + 1
        s = d.get("sector","Other")
        stats["by_sector"][s] = stats["by_sector"].get(s, 0) + 1
        st = d.get("stage", d.get("status",""))
        if st: stats["by_status"][st] = stats["by_status"].get(st, 0) + 1
        for ag in d.get("agreements",[]):
            ag_key = ag.split()[0][:15] if ag else ''
            if ag_key: stats["by_agreement"][ag_key] = stats["by_agreement"].get(ag_key, 0) + 1
        c = d.get("complainant","")
        r = d.get("respondent","")
        if "Saudi Arabia" in r or "Saudi Arabia" in c:
            stats["saudi_involvement"]["direct"] += 1
        if "Saudi Arabia" in str(d.get("third_parties",[])):
            stats["saudi_involvement"]["third_party"] += 1
        if d.get("saudi_relevance") == "HIGH":
            stats["saudi_involvement"]["high_relevance"] += 1
        if d.get("saudi_relevance") == "MEDIUM":
            stats["saudi_involvement"]["medium_relevance"] += 1
        if c: stats["top_complainants"][c] = stats["top_complainants"].get(c, 0) + 1
        if r: stats["top_respondents"][r] = stats["top_respondents"].get(r, 0) + 1
    return stats

# ─── Routes ───────────────────────────────────────────────────────────────────

# ── Embedded HTML (no file reading needed on Render) ──────────────────────────
INDEX_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>منصة رصد نزاعات WTO الذكية | Saudi WTO Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  /* ═══════════════════════════════════════════════════════════
     DESIGN SYSTEM — WTO Intelligence Platform
     Aesthetic: Dark intelligence / diplomatic refinement
     ═══════════════════════════════════════════════════════════ */
  :root {
    --bg-primary: #050c18;
    --bg-secondary: #0a1628;
    --bg-card: #0d1e35;
    --bg-glass: rgba(13, 30, 53, 0.85);
    --border: rgba(0, 162, 255, 0.12);
    --border-bright: rgba(0, 162, 255, 0.35);
    --accent-blue: #00a2ff;
    --accent-gold: #c9a84c;
    --accent-green: #00e5a0;
    --accent-red: #ff4b4b;
    --accent-orange: #ff8c42;
    --text-primary: #e8f0fe;
    --text-secondary: #8ba4c0;
    --text-muted: #445566;
    --saudi-green: #006c35;
    --saudi-gold: #c9a84c;
    --font-arabic: 'IBM Plex Sans Arabic', sans-serif;
    --font-latin: 'Space Grotesk', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius: 12px;
    --radius-lg: 20px;
    --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    --glow-blue: 0 0 24px rgba(0, 162, 255, 0.2);
    --glow-gold: 0 0 24px rgba(201, 168, 76, 0.2);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  html { scroll-behavior: smooth; }

  body {
    font-family: var(--font-arabic);
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    overflow-x: hidden;
    direction: rtl;
  }


  /* ─── Global select fix — ensure readable text in all dropdowns ─── */
  select {
    background-color: #0d1e35 !important;
    color: #e8f0fe !important;
  }
  select option {
    background-color: #0d1e35 !important;
    color: #e8f0fe !important;
  }
  select:focus { outline: none; }

  /* ─── Animated Background ─── */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: 
      radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0, 100, 200, 0.06) 0%, transparent 60%),
      radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0, 108, 53, 0.05) 0%, transparent 60%),
      radial-gradient(ellipse 40% 30% at 50% 50%, rgba(201, 168, 76, 0.03) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  /* ─── Header ─── */
  header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(5, 12, 24, 0.95);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
  }

  .header-inner {
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    gap: 2rem;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
  }

  .logo-emblem {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--saudi-green), var(--accent-blue));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 700;
    color: white;
    font-family: var(--font-latin);
  }

  .logo-text {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
  }

  .logo-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.5px;
  }

  .logo-subtitle {
    font-size: 11px;
    color: var(--accent-blue);
    font-family: var(--font-latin);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .header-nav {
    display: flex;
    gap: 4px;
  }

  .nav-btn {
    padding: 7px 16px;
    border-radius: 8px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-arabic);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-btn:hover, .nav-btn.active {
    background: rgba(0, 162, 255, 0.08);
    border-color: var(--border-bright);
    color: var(--accent-blue);
  }

  .nav-btn.saudi { color: var(--saudi-gold); }
  .nav-btn.saudi:hover, .nav-btn.saudi.active {
    background: rgba(201, 168, 76, 0.08);
    border-color: rgba(201, 168, 76, 0.3);
  }

  /* ─── Layout ─── */
  main {
    position: relative;
    z-index: 1;
    max-width: 1600px;
    margin: 0 auto;
    padding: 2rem;
  }

  .section { display: none; }
  .section.active { display: block; }

  /* ─── Hero / Search ─── */
  .hero {
    text-align: center;
    padding: 3rem 0 2rem;
    margin-bottom: 2rem;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 162, 255, 0.08);
    border: 1px solid rgba(0, 162, 255, 0.2);
    border-radius: 100px;
    padding: 4px 14px;
    font-size: 12px;
    color: var(--accent-blue);
    margin-bottom: 1.5rem;
    font-family: var(--font-latin);
    letter-spacing: 1px;
  }

  .hero h1 {
    font-size: clamp(1.8rem, 3.5vw, 2.8rem);
    font-weight: 700;
    background: linear-gradient(135deg, #e8f0fe 0%, #00a2ff 50%, #c9a84c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.8rem;
    line-height: 1.3;
  }

  .hero p {
    color: var(--text-secondary);
    font-size: 15px;
    max-width: 600px;
    margin: 0 auto 2rem;
    line-height: 1.7;
  }

  /* ─── Search Box ─── */
  .search-container {
    background: var(--bg-card);
    border: 1px solid var(--border-bright);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow), var(--glow-blue);
  }

  .search-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    margin-bottom: 1rem;
  }

  .search-main {
    position: relative;
  }

  .search-main input {
    width: 100%;
    padding: 12px 48px 12px 16px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-family: var(--font-arabic);
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s;
    direction: rtl;
  }

  .search-main input:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(0, 162, 255, 0.1);
  }

  .search-main::before {
    content: '🔍';
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
    pointer-events: none;
  }

  .search-filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
    margin-bottom: 1rem;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .filter-group label {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .filter-group select {
    padding: 8px 12px;
    background: #0d1e35;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: #e8f0fe;
    font-family: var(--font-arabic);
    font-size: 13px;
    outline: none;
    cursor: pointer;
    transition: border-color 0.2s;
    direction: rtl;
    -webkit-appearance: none;
    appearance: none;
  }

  .filter-group select option {
    background: #0d1e35;
    color: #e8f0fe;
  }

  .filter-group select:focus { border-color: var(--accent-blue); }
  .filter-group select:hover { border-color: var(--border-bright); }

  .search-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .logic-toggle {
    display: flex;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }

  .logic-toggle button {
    padding: 8px 16px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-latin);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .logic-toggle button.active {
    background: var(--accent-blue);
    color: white;
  }

  /* ─── Buttons ─── */
  .btn {
    padding: 10px 20px;
    border-radius: var(--radius);
    border: none;
    font-family: var(--font-arabic);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
  }

  .btn-primary {
    background: var(--accent-blue);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 162, 255, 0.3);
  }
  .btn-primary:hover { background: #0090e0; transform: translateY(-1px); }

  .btn-gold {
    background: var(--accent-gold);
    color: #0a0a0a;
    box-shadow: 0 4px 12px rgba(201, 168, 76, 0.3);
  }
  .btn-gold:hover { background: #b89640; transform: translateY(-1px); }

  .btn-outline {
    background: transparent;
    border: 1px solid var(--border-bright);
    color: var(--accent-blue);
  }
  .btn-outline:hover { background: rgba(0, 162, 255, 0.08); }

  .btn-green {
    background: var(--accent-green);
    color: #003020;
  }
  .btn-green:hover { background: #00cc90; transform: translateY(-1px); }

  .btn-sm { padding: 6px 12px; font-size: 12px; }

  /* ─── Cards Grid ─── */
  .results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }

  .results-count {
    font-size: 14px;
    color: var(--text-secondary);
  }

  .results-count strong {
    color: var(--accent-blue);
    font-family: var(--font-mono);
    font-size: 18px;
  }

  .disputes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 1.5rem;
  }

  /* ─── Dispute Card ─── */
  .dispute-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
  }

  .dispute-card::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 3px;
    height: 100%;
    background: var(--accent-blue);
    opacity: 0;
    transition: opacity 0.2s;
  }

  .dispute-card:hover {
    border-color: var(--border-bright);
    transform: translateY(-3px);
    box-shadow: var(--shadow), var(--glow-blue);
  }

  .dispute-card:hover::before { opacity: 1; }

  .dispute-card.saudi-high::before {
    background: var(--accent-gold);
    opacity: 0.6;
  }

  .dispute-card.saudi-high {
    border-color: rgba(201, 168, 76, 0.2);
  }

  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 1rem;
  }

  .ds-badge {
    background: rgba(0, 162, 255, 0.1);
    border: 1px solid rgba(0, 162, 255, 0.3);
    color: var(--accent-blue);
    padding: 3px 10px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
  }

  .relevance-badge {
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 700;
    font-family: var(--font-latin);
    letter-spacing: 0.5px;
    white-space: nowrap;
  }

  .rel-HIGH { background: rgba(201, 168, 76, 0.15); color: var(--accent-gold); border: 1px solid rgba(201, 168, 76, 0.3); }
  .rel-MEDIUM { background: rgba(0, 229, 160, 0.1); color: var(--accent-green); border: 1px solid rgba(0, 229, 160, 0.3); }
  .rel-LOW { background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border); }

  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.5;
    margin-bottom: 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-parties {
    display: flex;
    gap: 8px;
    margin-bottom: 0.8rem;
    flex-wrap: wrap;
  }

  .party-tag {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
  }

  .complainant-tag { background: rgba(255, 75, 75, 0.1); border: 1px solid rgba(255,75,75,0.2); color: #ff8080; }
  .respondent-tag { background: rgba(255, 140, 66, 0.1); border: 1px solid rgba(255,140,66,0.2); color: var(--accent-orange); }

  .card-agreements {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 0.8rem;
  }

  .agreement-chip {
    background: rgba(0, 162, 255, 0.06);
    border: 1px solid rgba(0, 162, 255, 0.15);
    color: var(--accent-blue);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 11px;
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  .stage-badge {
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    font-family: var(--font-latin);
  }

  .stage-Consultations { background: rgba(255, 200, 0, 0.1); color: #ffcc00; border: 1px solid rgba(255, 200, 0, 0.2); }
  .stage-Panel { background: rgba(0, 162, 255, 0.1); color: var(--accent-blue); border: 1px solid rgba(0,162,255,0.2); }
  .stage-Appeal { background: rgba(200, 0, 255, 0.1); color: #cc66ff; border: 1px solid rgba(200,0,255,0.2); }
  .stage-Implementation { background: rgba(0, 229, 160, 0.1); color: var(--accent-green); border: 1px solid rgba(0,229,160,0.2); }
  .stage-Completed { background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border); }
  .stage-Compliance { background: rgba(255, 140, 66, 0.1); color: var(--accent-orange); border: 1px solid rgba(255,140,66,0.2); }

  .card-year {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
  }

  /* ─── Modal ─── */
  .modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    z-index: 1000;
    overflow-y: auto;
    padding: 2rem;
  }

  .modal-overlay.open { display: flex; align-items: flex-start; justify-content: center; }

  .modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border-bright);
    border-radius: var(--radius-lg);
    max-width: 900px;
    width: 100%;
    box-shadow: 0 24px 80px rgba(0,0,0,0.6), var(--glow-blue);
    animation: modalIn 0.3s ease;
    margin: auto;
    overflow: hidden;
  }

  @keyframes modalIn {
    from { opacity: 0; transform: translateY(20px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  .modal-header {
    padding: 1.5rem 2rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    background: rgba(0, 162, 255, 0.03);
  }

  .modal-ds {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--accent-blue);
    margin-bottom: 4px;
  }

  .modal-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.4;
    max-width: 700px;
  }

  .modal-close {
    background: rgba(255,255,255,0.08);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    width: 32px;
    height: 32px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    flex-shrink: 0;
    transition: all 0.2s;
  }

  .modal-close:hover { background: rgba(255,75,75,0.1); color: #ff4b4b; border-color: rgba(255,75,75,0.3); }

  .modal-body { padding: 2rem; }

  .modal-tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0;
  }

  .modal-tab {
    padding: 8px 16px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-family: var(--font-arabic);
    font-size: 13px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .modal-tab.active {
    color: var(--accent-blue);
    border-bottom-color: var(--accent-blue);
  }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .info-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
  }

  .info-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    font-family: var(--font-latin);
  }

  .info-value {
    font-size: 14px;
    color: var(--text-primary);
    font-weight: 500;
  }

  .saudi-impact-box {
    background: rgba(201, 168, 76, 0.06);
    border: 1px solid rgba(201, 168, 76, 0.2);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
  }

  .saudi-impact-box .label {
    font-size: 11px;
    color: var(--accent-gold);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
    font-family: var(--font-latin);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .saudi-impact-box .value {
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.6;
  }

  .summary-box {
    background: rgba(0, 162, 255, 0.04);
    border: 1px solid rgba(0, 162, 255, 0.15);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1rem;
  }

  .summary-box p {
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-secondary);
  }

  /* ─── AI Panel ─── */
  .ai-panel {
    background: rgba(0,0,0,0.2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    min-height: 120px;
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-secondary);
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
  }

  .ai-loading {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--accent-blue);
    font-size: 14px;
    padding: 1rem;
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(0, 162, 255, 0.2);
    border-top-color: var(--accent-blue);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .ai-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  /* ─── Dashboard ─── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    text-align: center;
    transition: border-color 0.2s;
  }

  .stat-card:hover { border-color: var(--border-bright); }

  .stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    font-family: var(--font-mono);
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-gold));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin-bottom: 8px;
  }

  .stat-label {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
  }

  .chart-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bar-chart { display: flex; flex-direction: column; gap: 10px; }

  .bar-row {
    display: grid;
    grid-template-columns: 120px 1fr 40px;
    gap: 10px;
    align-items: center;
  }

  .bar-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    direction: ltr;
  }

  .bar-track {
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 100px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-gold));
    transition: width 1s ease;
  }

  .bar-count {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
    text-align: right;
  }

  /* ─── Saudi Watch Section ─── */
  .saudi-hero {
    background: linear-gradient(135deg, rgba(0, 108, 53, 0.1) 0%, rgba(201, 168, 76, 0.08) 100%);
    border: 1px solid rgba(201, 168, 76, 0.2);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin-bottom: 2rem;
    text-align: center;
  }

  .saudi-flag-strip {
    display: flex;
    justify-content: center;
    gap: 2px;
    margin-bottom: 1rem;
  }

  .flag-seg {
    width: 40px;
    height: 6px;
    border-radius: 3px;
  }

  .flag-green { background: var(--saudi-green); }
  .flag-gold { background: var(--saudi-gold); }
  .flag-white { background: rgba(255,255,255,0.6); }

  .saudi-hero h2 {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-gold);
    margin-bottom: 0.5rem;
  }

  .saudi-hero p {
    font-size: 13px;
    color: var(--text-secondary);
  }

  /* ─── AI Chat ─── */
  .chat-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 600px;
  }

  .chat-header {
    padding: 1rem 1.5rem;
    background: rgba(0, 162, 255, 0.05);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .ai-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--accent-blue), var(--saudi-green));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .message {
    max-width: 85%;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.7;
  }

  .message.user {
    background: rgba(0, 162, 255, 0.1);
    border: 1px solid rgba(0, 162, 255, 0.2);
    color: var(--text-primary);
    margin-right: auto;
    border-bottom-right-radius: 4px;
  }

  .message.assistant {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    margin-left: auto;
    border-bottom-left-radius: 4px;
    white-space: pre-wrap;
  }

  .chat-input-row {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    gap: 10px;
  }

  .chat-input {
    flex: 1;
    padding: 10px 14px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-family: var(--font-arabic);
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
    direction: rtl;
    resize: none;
  }

  .chat-input:focus { border-color: var(--accent-blue); }

  /* ─── Sources Page ─── */
  .sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .source-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    transition: all 0.2s;
    text-decoration: none;
    display: block;
  }

  .source-card:hover {
    border-color: var(--border-bright);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
  }

  .source-name {
    font-size: 14px;
    font-weight: 700;
    color: var(--accent-blue);
    margin-bottom: 6px;
  }

  .source-desc {
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 8px;
    line-height: 1.5;
  }

  .source-use {
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.5;
    padding-top: 8px;
    border-top: 1px solid var(--border);
  }

  .section-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  /* ─── Empty State ─── */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
  }

  .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
  .empty-state h3 { font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--text-secondary); }
  .empty-state p { font-size: 13px; }

  /* ─── Toast ─── */
  .toast {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: var(--bg-card);
    border: 1px solid var(--border-bright);
    border-radius: var(--radius);
    padding: 12px 24px;
    font-size: 14px;
    color: var(--text-primary);
    z-index: 9999;
    transition: transform 0.3s;
    box-shadow: var(--shadow);
  }

  .toast.show { transform: translateX(-50%) translateY(0); }

  /* ─── Scrollbar ─── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(0, 162, 255, 0.2); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(0, 162, 255, 0.4); }

  /* ─── Responsive ─── */
  @media (max-width: 768px) {
    main { padding: 1rem; }
    .disputes-grid { grid-template-columns: 1fr; }
    .charts-row { grid-template-columns: 1fr; }
    .info-grid { grid-template-columns: 1fr; }
    .header-nav { overflow-x: auto; }
    .search-filters { grid-template-columns: 1fr 1fr; }
    .modal { margin: 0; border-radius: 0; }
  }
</style>
</head>
<body>

<!-- ─── Header ─────────────────────────────────────────── -->
<header>
  <div class="header-inner">
    <a class="logo" href="#" onclick="showSection('search')">
      <div class="logo-emblem">W</div>
      <div class="logo-text">
        <span class="logo-title">منصة WTO الذكية</span>
        <span class="logo-subtitle">Dispute Intelligence Platform</span>
      </div>
    </a>
    <nav class="header-nav">
      <button class="nav-btn active" id="nav-search" onclick="showSection('search')">🔍 البحث في النزاعات</button>
      <button class="nav-btn" id="nav-dashboard" onclick="showSection('dashboard')">📊 لوحة التحكم</button>
      <button class="nav-btn saudi" id="nav-saudi" onclick="showSection('saudi')">🇸🇦 Saudi Watch</button>
      <button class="nav-btn" id="nav-chat" onclick="showSection('chat')">🤖 المساعد القانوني</button>
      <button class="nav-btn" id="nav-sources" onclick="showSection('sources')">📚 المصادر الرسمية</button>
    </nav>
  </div>
</header>

<!-- ─── Main ────────────────────────────────────────────── -->
<main>

  <!-- ══════════════════ SEARCH SECTION ══════════════════ -->
  <section class="section active" id="section-search">
    <div class="hero">
      <div class="hero-badge">⚖️ WTO DISPUTE SETTLEMENT INTELLIGENCE</div>
      <h1>منصة رصد نزاعات منظمة التجارة العالمية</h1>
      <p>بحث قانوني متقدم، تحليل ذكاء اصطناعي، ومتابعة شاملة لقضايا WTO وأثرها على المملكة العربية السعودية</p>
    </div>

    <div class="search-container">
      <div class="search-row">
        <div class="search-main">
          <input type="text" id="search-q" placeholder="ابحث بالموضوع أو الاتفاقية أو المادة القانونية... (CBAM, Steel, TRIPS, SCM...)" oninput="debounceSearch()">
        </div>
        <div class="search-actions">
          <div class="logic-toggle">
            <button id="logic-and" class="active" onclick="setLogic('AND')">AND</button>
            <button id="logic-or" onclick="setLogic('OR')">OR</button>
          </div>
          <button class="btn btn-primary" onclick="runSearch()">🔍 بحث</button>
          <button class="btn btn-outline" onclick="clearSearch()">مسح</button>
        </div>
      </div>

      <div class="search-filters">
        <div class="filter-group">
          <label>السنة</label>
          <select id="filter-year" onchange="runSearch()">
            <option value="">الكل</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
            <option value="2021">2021</option>
            <option value="2020">2020</option>
            <option value="2019">2019</option>
            <option value="2018">2018</option>
            <option value="2016">2016</option>
          </select>
        </div>
        <div class="filter-group">
          <label>الاتفاقية</label>
          <select id="filter-agreement" onchange="runSearch()">
            <option value="">الكل</option>
            <option value="GATT">GATT 1994</option>
            <option value="GATS">GATS</option>
            <option value="TRIPS">TRIPS</option>
            <option value="SCM">SCM Agreement</option>
            <option value="Anti-Dumping">Anti-Dumping</option>
            <option value="Safeguards">Safeguards</option>
            <option value="SPS">SPS Agreement</option>
            <option value="TBT">TBT Agreement</option>
          </select>
        </div>
        <div class="filter-group">
          <label>القطاع</label>
          <select id="filter-sector" onchange="runSearch()">
            <option value="">الكل</option>
            <option value="Energy">الطاقة والبيئة</option>
            <option value="Petrochemical">البتروكيماويات</option>
            <option value="Metals">المعادن والصلب</option>
            <option value="Agriculture">الزراعة والغذاء</option>
            <option value="Services">الخدمات</option>
            <option value="Intellectual Property">الملكية الفكرية</option>
            <option value="Renewable">الطاقة المتجددة</option>
          </select>
        </div>
        <div class="filter-group">
          <label>الدولة الشاكية</label>
          <select id="filter-complainant" onchange="runSearch()">
            <option value="">الكل</option>
          </select>
        </div>
        <div class="filter-group">
          <label>الدولة المدعى عليها</label>
          <select id="filter-respondent" onchange="runSearch()">
            <option value="">الكل</option>
          </select>
        </div>
        <div class="filter-group">
          <label>المرحلة الإجرائية</label>
          <select id="filter-status" onchange="runSearch()">
            <option value="">الكل</option>
            <option value="Consultations">Consultations</option>
            <option value="Panel">Panel</option>
            <option value="Appeal">Appeal</option>
            <option value="Implementation">Implementation</option>
            <option value="Compliance">Compliance</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
        <div class="filter-group">
          <label>🇸🇦 صلة بالمملكة</label>
          <select id="filter-saudi" onchange="runSearch()">
            <option value="">الكل</option>
            <option value="HIGH">عالية</option>
            <option value="MEDIUM">متوسطة</option>
            <option value="LOW">منخفضة</option>
          </select>
        </div>
        <div class="filter-group">
          <label>📂 مصدر البيانات</label>
          <select id="filter-source" onchange="runSearch()">
            <option value="all">الكل (194 قضية)</option>
            <option value="pdf">📄 PDF رسمي 1995-2022 (186)</option>
            <option value="curated">⭐ منتقى سعودي (8)</option>
          </select>
        </div>
      </div>
      <div style="font-size:11px;color:var(--text-muted);display:flex;align-items:center;gap:6px;padding-top:4px">
        <span style="color:var(--accent-green)">●</span>
        <span id="source-counts">الكل: 194 | منشور PDF رسمي WTO 1995-2022: 186 | سعودي مُنتقى: 8</span>
      </div>
    </div>

    <div class="results-header">
      <div class="results-count">عُثر على <strong id="result-count">—</strong> قضية</div>
      <div style="display:flex;gap:8px;align-items:center">
        <span style="font-size:12px;color:var(--text-muted)">ترتيب حسب:</span>
        <select id="sort-by" onchange="runSearch()" style="background:#0d1e35;border:1px solid var(--border);border-radius:8px;color:#e8f0fe;font-family:var(--font-arabic);font-size:12px;padding:6px 10px;outline:none;">
          <option value="relevance">الصلة بالمملكة</option>
          <option value="year">السنة</option>
          <option value="ds">رقم DS</option>
        </select>
      </div>
    </div>

    <div class="disputes-grid" id="disputes-grid">
      <div class="empty-state" style="grid-column:1/-1">
        <div class="spinner"></div>
        <p style="margin-top:12px;color:var(--text-muted);font-size:13px">جارٍ تحميل 194 قضية من منشور WTO الرسمي 1995-2022…</p>
      </div>
    </div>
    <div id="pagination"></div>
  </section>

  <!-- ══════════════════ DASHBOARD SECTION ══════════════════ -->
  <section class="section" id="section-dashboard">
    <div style="margin-bottom:2rem">
      <h2 style="font-size:1.4rem;font-weight:700;color:var(--text-primary);margin-bottom:0.5rem">📊 لوحة التحكم التحليلية</h2>
      <p style="color:var(--text-secondary);font-size:13px">إحصاءات شاملة لنزاعات منظمة التجارة العالمية مع تحليل خاص بمصالح المملكة</p>
    </div>

    <div class="stats-grid" id="stats-grid">
      <div class="stat-card"><div class="stat-value" id="stat-total">—</div><div class="stat-label">إجمالي القضايا</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-saudi-direct">—</div><div class="stat-label">قضايا المملكة المباشرة</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-saudi-third">—</div><div class="stat-label">المملكة كطرف ثالث</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-high-rel">—</div><div class="stat-label">قضايا ذات صلة عالية</div></div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">⚖️ الاتفاقيات الأكثر استناداً</div>
        <div class="bar-chart" id="chart-agreements"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🏭 توزيع القضايا حسب القطاع</div>
        <div class="bar-chart" id="chart-sectors"></div>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">📅 القضايا حسب السنة</div>
        <div class="bar-chart" id="chart-years"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">🔄 المرحلة الإجرائية</div>
        <div class="bar-chart" id="chart-status"></div>
      </div>
    </div>
  </section>

  <!-- ══════════════════ SAUDI WATCH SECTION ══════════════════ -->
  <section class="section" id="section-saudi">
    <div class="saudi-hero">
      <div class="saudi-flag-strip">
        <div class="flag-seg flag-green"></div>
        <div class="flag-seg flag-gold"></div>
        <div class="flag-seg flag-green"></div>
      </div>
      <h2>🇸🇦 Saudi WTO Disputes Watch</h2>
      <p>رصد وتحليل ومتابعة القضايا والنزاعات في WTO ذات الأثر على مصالح المملكة العربية السعودية ودول مجلس التعاون الخليجي</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:2rem">
      <div style="background:rgba(201,168,76,0.06);border:1px solid rgba(201,168,76,0.2);border-radius:var(--radius-lg);padding:1.25rem;text-align:center">
        <div style="font-size:2rem;margin-bottom:6px">⚡</div>
        <div style="font-size:13px;font-weight:700;color:var(--accent-gold);margin-bottom:4px">قضايا CBAM والكربون</div>
        <div style="font-size:12px;color:var(--text-muted)">تأثير مباشر على الصادرات النفطية والبتروكيماوية</div>
      </div>
      <div style="background:rgba(0,229,160,0.06);border:1px solid rgba(0,229,160,0.15);border-radius:var(--radius-lg);padding:1.25rem;text-align:center">
        <div style="font-size:2rem;margin-bottom:6px">🏗️</div>
        <div style="font-size:13px;font-weight:700;color:var(--accent-green);margin-bottom:4px">الصلب والألمنيوم والمعادن</div>
        <div style="font-size:12px;color:var(--text-muted)">نزاعات تؤثر على تنافسية الصادرات السعودية</div>
      </div>
      <div style="background:rgba(0,162,255,0.06);border:1px solid rgba(0,162,255,0.15);border-radius:var(--radius-lg);padding:1.25rem;text-align:center">
        <div style="font-size:2rem;margin-bottom:6px">🌿</div>
        <div style="font-size:13px;font-weight:700;color:var(--accent-blue);margin-bottom:4px">الطاقة المتجددة والهيدروجين</div>
        <div style="font-size:12px;color:var(--text-muted)">نزاعات تدعم رؤية 2030 وأهداف التنويع</div>
      </div>
    </div>

    <div class="disputes-grid" id="saudi-disputes-grid">
      <div class="empty-state" style="grid-column:1/-1">
        <div class="spinner"></div>
      </div>
    </div>
  </section>

  <!-- ══════════════════ AI CHAT SECTION ══════════════════ -->
  <section class="section" id="section-chat">
    <div style="margin-bottom:1.5rem">
      <h2 style="font-size:1.4rem;font-weight:700;color:var(--text-primary);margin-bottom:0.5rem">🤖 المساعد القانوني الذكي — WTO Legal AI</h2>
      <p style="color:var(--text-secondary);font-size:13px">مستشار قانوني متخصص في اتفاقيات WTO وتأثيرها على المملكة العربية السعودية</p>
    </div>

    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:1rem">
      <button class="btn btn-outline btn-sm" onclick="insertChat('ما هي قضايا CBAM وتأثيرها على الصادرات السعودية؟')">CBAM والصادرات السعودية</button>
      <button class="btn btn-outline btn-sm" onclick="insertChat('اشرح الفرق بين المادتين I وIII من اتفاقية GATT')">GATT Art. I vs III</button>
      <button class="btn btn-outline btn-sm" onclick="insertChat('ما موقف المملكة في قضية DS590؟')">قضية DS590</button>
      <button class="btn btn-outline btn-sm" onclick="insertChat('ما هي اتفاقية SCM وكيف تؤثر على الدعم الصناعي السعودي؟')">اتفاقية SCM</button>
      <button class="btn btn-outline btn-sm" onclick="insertChat('ما هي أحدث القضايا المتعلقة بالطاقة المتجددة في WTO؟')">نزاعات الطاقة المتجددة</button>
    </div>

    <div class="chat-container" id="chat-container">
      <div class="chat-header">
        <div class="ai-avatar">⚖️</div>
        <div>
          <div style="font-size:14px;font-weight:700;color:var(--text-primary)">WTO Legal Intelligence</div>
          <div style="font-size:12px;color:var(--accent-green)">● متصل — جاهز للمساعدة القانونية</div>
        </div>
        <div style="margin-right:auto;display:flex;gap:6px">
          <button class="btn btn-outline btn-sm" onclick="setLang('ar')" id="lang-ar" style="border-color:rgba(201,168,76,0.3);color:var(--accent-gold)">🇸🇦 عربي</button>
          <button class="btn btn-outline btn-sm" onclick="setLang('en')" id="lang-en">🇺🇸 English</button>
        </div>
      </div>
      <div class="chat-messages" id="chat-messages">
        <div class="message assistant">
مرحباً! أنا مستشارك القانوني المتخصص في نزاعات منظمة التجارة العالمية (WTO).

يمكنني مساعدتك في:
• تحليل القضايا وفق اتفاقيات WTO (GATT, GATS, TRIPS, SCM, TBT, SPS…)
• تقييم تأثير النزاعات على المصالح التجارية السعودية
• إعداد مذكرات قانونية ومخصصة للجهات الحكومية والقطاع الخاص
• شرح إجراءات تسوية المنازعات في DSU
• تحليل قضايا CBAM وتداعياتها على صادرات المملكة

كيف يمكنني مساعدتك؟
        </div>
      </div>
      <div class="chat-input-row">
        <textarea class="chat-input" id="chat-input" rows="2" placeholder="اسأل عن أي قضية WTO أو اتفاقية أو تأثير على المملكة..." onkeydown="handleChatKey(event)"></textarea>
        <button class="btn btn-primary" onclick="sendChat()">إرسال ↵</button>
      </div>
    </div>
  </section>

  <!-- ══════════════════ SOURCES SECTION ══════════════════ -->
  <section class="section" id="section-sources">
    <div style="margin-bottom:2rem">
      <h2 style="font-size:1.4rem;font-weight:700;color:var(--text-primary);margin-bottom:0.5rem">📚 المصادر الرسمية وأدوات البحث</h2>
      <p style="color:var(--text-secondary);font-size:13px">قائمة شاملة بالمصادر الرسمية لمتابعة وتحليل نزاعات WTO والتجارة الدولية</p>
    </div>

    <div style="margin-bottom:2rem">
      <div class="section-title">🌐 منظمة التجارة العالمية — المصادر الرسمية</div>
      <div class="sources-grid" id="sources-wto"></div>
    </div>

    <div style="margin-bottom:2rem">
      <div class="section-title">📡 منصات الرصد والتنبيهات</div>
      <div class="sources-grid" id="sources-monitor"></div>
    </div>

    <div style="margin-bottom:2rem">
      <div class="section-title">🇸🇦 الجهات السعودية الرسمية</div>
      <div class="sources-grid" id="sources-saudi"></div>
    </div>

    <div>
      <div class="section-title">📈 أدوات التحليل الدولية</div>
      <div class="sources-grid" id="sources-analysis"></div>
    </div>
  </section>

</main>

<!-- ─── Dispute Detail Modal ────────────────────────────── -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModalIfBg(event)">
  <div class="modal" id="modal">
    <div class="modal-header">
      <div>
        <div class="modal-ds" id="modal-ds"></div>
        <div class="modal-title" id="modal-title"></div>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body">
      <div class="modal-tabs">
        <button class="modal-tab active" onclick="showTab('info')">📋 معلومات القضية</button>
        <button class="modal-tab" onclick="showTab('summary')">📝 الملخص القانوني</button>
        <button class="modal-tab" onclick="showTab('ai')">🤖 التحليل الذكي</button>
        <button class="modal-tab" onclick="showTab('memo')">📄 مذكرة تنفيذية</button>
      </div>

      <!-- Info Tab -->
      <div class="tab-content active" id="tab-info">
        <div class="info-grid" id="info-grid"></div>
        <div class="saudi-impact-box" id="saudi-impact-box"></div>
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px">الاتفاقيات والمواد القانونية</div>
          <div id="agreements-list" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1rem"></div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px">الأطراف الثالثة</div>
          <div id="third-parties-list" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1.5rem"></div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <a id="wto-link" href="#" target="_blank" class="btn btn-outline btn-sm">🔗 صفحة WTO الرسمية</a>
          <button class="btn btn-gold btn-sm" onclick="showTab('ai');generateAI()">🤖 تحليل بالذكاء الاصطناعي</button>
          <button class="btn btn-outline btn-sm" onclick="showTab('memo');generateMemo()">📄 مذكرة قانونية</button>
        </div>
      </div>

      <!-- Summary Tab -->
      <div class="tab-content" id="tab-summary">
        <div style="margin-bottom:1rem">
          <div class="section-title">📝 الملخص بالعربية</div>
          <div class="summary-box"><p id="summary-ar" style="color:var(--text-secondary);font-size:13px;line-height:1.8"></p></div>
        </div>
        <div>
          <div class="section-title">📝 English Summary</div>
          <div class="summary-box"><p id="summary-en"></p></div>
        </div>
      </div>

      <!-- AI Tab -->
      <div class="tab-content" id="tab-ai">
        <div class="ai-actions">
          <button class="btn btn-gold btn-sm" onclick="generateAI('ar')">🤖 تحليل بالعربية</button>
          <button class="btn btn-outline btn-sm" onclick="generateAI('en')">🤖 Analyze in English</button>
        </div>
        <div class="ai-panel" id="ai-panel">اضغط على "تحليل" لتوليد تحليل قانوني ذكي لهذه القضية...</div>
      </div>

      <!-- Memo Tab -->
      <div class="tab-content" id="tab-memo">
        <div class="ai-actions">
          <button class="btn btn-gold btn-sm" onclick="generateMemo('ar','government')">🏛️ مذكرة حكومية — عربي</button>
          <button class="btn btn-outline btn-sm" onclick="generateMemo('en','private')">💼 Private Sector Memo</button>
          <button class="btn btn-green btn-sm" onclick="copyMemo()">📋 نسخ المذكرة</button>
        </div>
        <div class="ai-panel" id="memo-panel">اضغط لإنشاء مذكرة قانونية تنفيذية مخصصة...</div>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<!-- ─── JavaScript ─────────────────────────────────────── -->
<script>
// ═══════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════
let currentDispute = null;
let searchLogic = 'AND';
let chatLang = 'ar';
let chatHistory = [];
let debounceTimer = null;

// ═══════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('section-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
  if (name === 'dashboard') loadDashboard();
  if (name === 'saudi') loadSaudiWatch();
  if (name === 'sources') loadSources();
}

// ═══════════════════════════════════════════════════════════
// SEARCH
// ═══════════════════════════════════════════════════════════
function debounceSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runSearch, 400);
}

function setLogic(l) {
  searchLogic = l;
  document.getElementById('logic-and').classList.toggle('active', l === 'AND');
  document.getElementById('logic-or').classList.toggle('active', l === 'OR');
  runSearch();
}

function clearSearch() {
  document.getElementById('search-q').value = '';
  document.getElementById('filter-year').value = '';
  document.getElementById('filter-agreement').value = '';
  document.getElementById('filter-sector').value = '';
  document.getElementById('filter-complainant').value = '';
  document.getElementById('filter-respondent').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-saudi').value = '';
  runSearch();
}

let currentPage = 1;
const PER_PAGE = 30;

function getVal(id, fallback='') {
  const el = document.getElementById(id);
  return el ? el.value : fallback;
}

async function runSearch(page = 1) {
  currentPage = page;
  const params = new URLSearchParams({
    q: getVal('search-q'),
    year: getVal('filter-year'),
    agreement: getVal('filter-agreement'),
    sector: getVal('filter-sector'),
    complainant: getVal('filter-complainant'),
    respondent: getVal('filter-respondent'),
    status: getVal('filter-status'),
    saudi_relevance: getVal('filter-saudi'),
    logic: searchLogic,
    source: getVal('filter-source', 'all'),
    page: page,
    per_page: PER_PAGE
  });

  const grid = document.getElementById('disputes-grid');
  grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><div class="spinner"></div><p style="margin-top:12px">جارٍ البحث في ' + (document.getElementById('filter-source')?.value === 'pdf' ? '186 قضية رسمية من منشور WTO 1995-2022' : '194 قضية') + '...</p></div>';

  try {
    const res = await fetch('/api/disputes?' + params);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch(pe) {
      console.error('Response is not JSON:', text.substring(0, 200));
      throw new Error('Server returned non-JSON response');
    }
    renderDisputes(data.disputes, 'disputes-grid');
    const rcnt = document.getElementById('result-count');
    if (rcnt) rcnt.textContent = data.total;
    renderPagination(data.total, data.page, data.pages);
    if (data.source_counts) {
      const srcEl = document.getElementById('source-counts');
      if (srcEl) srcEl.textContent = `الكل: ${data.source_counts.all} | منشور PDF: ${data.source_counts.pdf} | سعودي مُنتقى: ${data.source_counts.curated}`;
    }
  } catch(e) {
    console.error('runSearch error:', e);
    if (grid) grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">⚠️</div><h3>خطأ في الاتصال</h3><p style="font-size:12px;color:var(--text-muted)">${e.message}</p><button class="btn btn-outline" style="margin-top:1rem" onclick="runSearch()">🔄 إعادة المحاولة</button></div>`;
  }
}

function renderPagination(total, currentPg, totalPages) {
  const el = document.getElementById('pagination');
  if (!el || totalPages <= 1) { if(el) el.innerHTML = ''; return; }
  let html = '<div style="display:flex;align-items:center;gap:8px;justify-content:center;margin-top:1.5rem;flex-wrap:wrap">';
  if (currentPg > 1) html += `<button class="btn btn-outline" style="padding:6px 14px;font-size:12px" onclick="runSearch(${currentPg-1})">→ السابق</button>`;
  const start = Math.max(1, currentPg - 2);
  const end = Math.min(totalPages, currentPg + 2);
  if (start > 1) html += `<button class="btn btn-outline" style="padding:6px 10px;font-size:12px" onclick="runSearch(1)">1</button><span style="color:var(--text-muted)">…</span>`;
  for (let i = start; i <= end; i++) {
    html += `<button class="btn ${i===currentPg?'btn-primary':'btn-outline'}" style="padding:6px 10px;font-size:12px;min-width:36px" onclick="runSearch(${i})">${i}</button>`;
  }
  if (end < totalPages) html += `<span style="color:var(--text-muted)">…</span><button class="btn btn-outline" style="padding:6px 10px;font-size:12px" onclick="runSearch(${totalPages})">${totalPages}</button>`;
  if (currentPg < totalPages) html += `<button class="btn btn-outline" style="padding:6px 14px;font-size:12px" onclick="runSearch(${currentPg+1})">← التالي</button>`;
  html += `<span style="font-size:12px;color:var(--text-muted);margin-right:8px">صفحة ${currentPg} من ${totalPages} (${total} قضية)</span>`;
  html += '</div>';
  el.innerHTML = html;
}

function renderDisputes(disputes, containerId) {
  const grid = document.getElementById(containerId);
  if (!disputes || !disputes.length) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><div class="icon">🔍</div><h3>لا توجد نتائج</h3><p>جرّب تغيير معايير البحث</p></div>';
    return;
  }

  grid.innerHTML = disputes.map(d => {
    const stage = d.stage || d.status || 'N/A';
    const stageClass = 'stage-' + stage.replace(/[\\s\\(\\)\\.]/g,'');
    const isPDF = d.source && d.source.includes('1995-2022');
    const srcBadge = isPDF
      ? `<span style="padding:2px 7px;border-radius:4px;font-size:10px;background:rgba(0,229,160,0.08);border:1px solid rgba(0,229,160,0.2);color:var(--accent-green);font-family:var(--font-mono)">📄 PDF</span>`
      : `<span style="padding:2px 7px;border-radius:4px;font-size:10px;background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.2);color:var(--accent-gold);font-family:var(--font-mono)">⭐ منتقى</span>`;
    return `
    <div class="dispute-card ${d.saudi_relevance === 'HIGH' ? 'saudi-high' : ''}" onclick="openModal('${d.ds_number}')">
      <div class="card-header">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span class="ds-badge">${d.ds_number}</span>
          ${srcBadge}
        </div>
        <span class="relevance-badge rel-${d.saudi_relevance || 'LOW'}">🇸🇦 ${d.saudi_relevance || 'LOW'}</span>
      </div>
      <div class="card-title">${d.title}</div>
      <div class="card-parties">
        <span class="party-tag complainant-tag">⚔️ ${(d.complainant||'').substring(0,30)}</span>
        <span class="party-tag respondent-tag">🛡️ ${(d.respondent||'').substring(0,30)}</span>
      </div>
      <div class="card-agreements">
        ${(d.agreements||[]).slice(0,3).map(a => `<span class="agreement-chip">${a.substring(0,25)}</span>`).join('')}
      </div>
      <div class="card-footer">
        <span class="stage-badge ${stageClass}">${stage}</span>
        <span class="card-year">${d.year || '—'}</span>
      </div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════
async function loadDashboard() {
  try {
    const res = await fetch('/api/stats');
    const s = await res.json();

    document.getElementById('stat-total').textContent = s.total;
    document.getElementById('stat-total').textContent = s.total;
    document.getElementById('stat-saudi-direct').textContent = s.saudi_involvement.direct;
    document.getElementById('stat-saudi-third').textContent = s.saudi_involvement.third_party;
    document.getElementById('stat-high-rel').textContent = s.saudi_involvement.high_relevance;

    renderBarChart('chart-agreements', s.by_agreement);
    renderBarChart('chart-sectors', s.by_sector);
    renderBarChart('chart-years', s.by_year);
    renderBarChart('chart-status', s.by_status);
  } catch(e) { console.error(e); }
}

function renderBarChart(containerId, data) {
  const el = document.getElementById(containerId);
  const entries = Object.entries(data).sort((a,b) => b[1] - a[1]).slice(0, 8);
  const max = Math.max(...entries.map(e => e[1]));
  el.innerHTML = entries.map(([k, v]) => `
    <div class="bar-row">
      <div class="bar-label">${k}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(v/max*100).toFixed(1)}%"></div></div>
      <div class="bar-count">${v}</div>
    </div>
  `).join('');
}

// ═══════════════════════════════════════════════════════════
// SAUDI WATCH
// ═══════════════════════════════════════════════════════════
async function loadSaudiWatch() {
  try {
    const res = await fetch('/api/saudi-watch');
    const data = await res.json();
    renderDisputes(data.disputes, 'saudi-disputes-grid');
  } catch(e) { console.error(e); }
}

// ═══════════════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════════════
async function openModal(dsNum) {
  try {
    const res = await fetch('/api/disputes/' + dsNum);
    currentDispute = await res.json();
    if (currentDispute.error) return;

    const _stage = currentDispute.stage || currentDispute.status || 'Completed';
    const _stageClass = _stage.replace(/[\\s\\(\\)\\.]/g,'');
    document.getElementById('modal-ds').textContent = currentDispute.ds_number;
    document.getElementById('modal-title').textContent = currentDispute.title;

    document.getElementById('info-grid').innerHTML = `
      <div class="info-item"><div class="info-label">الدولة الشاكية</div><div class="info-value">⚔️ ${currentDispute.complainant}</div></div>
      <div class="info-item"><div class="info-label">الدولة المدعى عليها</div><div class="info-value">🛡️ ${currentDispute.respondent}</div></div>
      <div class="info-item"><div class="info-label">المرحلة الإجرائية</div><div class="info-value"><span class="stage-badge stage-${_stageClass}">${_stage}</span></div></div>
      <div class="info-item"><div class="info-label">السنة / تاريخ الطلب</div><div class="info-value">${currentDispute.year} — ${currentDispute.request_date || '—'}</div></div>
      <div class="info-item"><div class="info-label">القطاع</div><div class="info-value">${currentDispute.sector}</div></div>
      <div class="info-item"><div class="info-label">الصلة بالمملكة</div><div class="info-value"><span class="relevance-badge rel-${currentDispute.saudi_relevance}">${currentDispute.saudi_relevance}</span></div></div>
    `;

    document.getElementById('saudi-impact-box').innerHTML = `
      <div class="label">🇸🇦 تحليل الأثر على المملكة العربية السعودية</div>
      <div class="value">${currentDispute.saudi_impact || 'غير محدد'}</div>
    `;

    document.getElementById('agreements-list').innerHTML =
      currentDispute.agreements.map(a => `<span class="agreement-chip">${a}</span>`).join('') +
      (currentDispute.articles || []).map(a => `<span class="agreement-chip" style="background:rgba(201,168,76,0.1);border-color:rgba(201,168,76,0.2);color:var(--accent-gold)">${a}</span>`).join('');

    const tpList = currentDispute.third_parties || [];
    document.getElementById('third-parties-list').innerHTML = tpList.length
      ? tpList.map(p => `<span style="padding:3px 10px;border-radius:6px;font-size:12px;background:rgba(255,255,255,0.04);border:1px solid var(--border);color:var(--text-secondary)">${p}</span>`).join('')
      : '<span style="font-size:12px;color:var(--text-muted)">لا توجد أطراف ثالثة مسجلة لهذه القضية في قاعدة البيانات الحالية</span>';

    document.getElementById('wto-link').href = `https://www.wto.org/english/tratop_e/dispu_e/cases_e/${currentDispute.ds_number.toLowerCase()}_e.htm`;
    document.getElementById('summary-ar').textContent = currentDispute.summary_ar;
    document.getElementById('summary-en').textContent = currentDispute.summary_en;
    document.getElementById('ai-panel').textContent = 'اضغط على "تحليل" لتوليد تحليل قانوني ذكي لهذه القضية...';
    document.getElementById('memo-panel').textContent = 'اضغط لإنشاء مذكرة قانونية تنفيذية مخصصة...';

    // Show Arabic summary or fallback message
    const arEl = document.getElementById('summary-ar');
    const enEl = document.getElementById('summary-en');
    if (arEl) {
      if (currentDispute.summary_ar && currentDispute.summary_ar.trim()) {
        arEl.textContent = currentDispute.summary_ar;
      } else {
        arEl.style.color = 'var(--text-muted)';
        arEl.textContent = 'الملخص العربي غير متوفر لهذه القضية — استخدم تبويب التحليل الذكي لتوليد ملخص عربي تلقائي.';
      }
    }
    if (enEl) enEl.textContent = currentDispute.summary_en || '';
    showTab('info');
    document.getElementById('modal-overlay').classList.add('open');
  } catch(e) { console.error(e); }
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  currentDispute = null;
}

function closeModalIfBg(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  const tabs = document.querySelectorAll('.modal-tab');
  const map = {info:0, summary:1, ai:2, memo:3};
  if (tabs[map[name]]) tabs[map[name]].classList.add('active');
}

// ═══════════════════════════════════════════════════════════
// AI FUNCTIONS
// ═══════════════════════════════════════════════════════════
async function generateAI(lang = 'ar') {
  if (!currentDispute) return;
  const panel = document.getElementById('ai-panel');
  panel.innerHTML = '<div class="ai-loading"><div class="spinner"></div>جارٍ تحليل القضية بالذكاء الاصطناعي...</div>';
  try {
    const res = await fetch('/api/ai/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ds_number: currentDispute.ds_number, language: lang})
    });
    const data = await res.json();
    if (data.error) { panel.textContent = '⚠️ ' + data.error; return; }
    panel.textContent = data.analysis;
  } catch(e) {
    panel.textContent = '⚠️ خطأ في الاتصال بنظام الذكاء الاصطناعي. تأكد من إعداد ANTHROPIC_API_KEY.';
  }
}

async function generateMemo(lang = 'ar', audience = 'government') {
  if (!currentDispute) return;
  const panel = document.getElementById('memo-panel');
  panel.innerHTML = '<div class="ai-loading"><div class="spinner"></div>جارٍ إعداد المذكرة القانونية التنفيذية...</div>';
  try {
    const res = await fetch('/api/ai/memo', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ds_number: currentDispute.ds_number, language: lang, audience: audience})
    });
    const data = await res.json();
    if (data.error) { panel.textContent = '⚠️ ' + data.error; return; }
    panel.textContent = data.memo;
  } catch(e) {
    panel.textContent = '⚠️ خطأ في الاتصال. تأكد من إعداد ANTHROPIC_API_KEY.';
  }
}

function copyMemo() {
  const text = document.getElementById('memo-panel').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('✅ تم نسخ المذكرة'));
}

// ═══════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════
function setLang(l) {
  chatLang = l;
  document.getElementById('lang-ar').style.borderColor = l === 'ar' ? 'rgba(201,168,76,0.5)' : '';
  document.getElementById('lang-en').style.borderColor = l === 'en' ? 'rgba(0,162,255,0.5)' : '';
}

function insertChat(text) {
  document.getElementById('chat-input').value = text;
  showSection('chat');
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  appendMessage('user', text);
  chatHistory.push({role: 'user', content: text});

  const thinkingId = appendMessage('assistant', '<div class="ai-loading"><div class="spinner"></div>يجري التفكير...</div>', true);

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({messages: chatHistory, language: chatLang})
    });
    const data = await res.json();
    const reply = data.response || data.error || 'حدث خطأ';
    updateMessage(thinkingId, reply);
    chatHistory.push({role: 'assistant', content: reply});
  } catch(e) {
    updateMessage(thinkingId, '⚠️ خطأ في الاتصال. تأكد من إعداد ANTHROPIC_API_KEY في بيئة التشغيل.');
  }
}

let msgId = 0;
function appendMessage(role, html, isLoading = false) {
  const id = 'msg-' + (++msgId);
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'message ' + role;
  div.id = id;
  if (isLoading) div.innerHTML = html;
  else div.textContent = html;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function updateMessage(id, text) {
  const el = document.getElementById(id);
  if (el) { el.textContent = text; el.closest('.chat-messages').scrollTop = 99999; }
}

// ═══════════════════════════════════════════════════════════
// SOURCES
// ═══════════════════════════════════════════════════════════
async function loadSources() {
  try {
    const res = await fetch('/api/sources');
    const data = await res.json();

    renderSources('sources-wto', data.wto_official);
    renderSources('sources-monitor', data.monitoring);
    renderSources('sources-saudi', data.saudi_official);
    renderSources('sources-analysis', data.analysis);
  } catch(e) {}
}

function renderSources(id, sources) {
  document.getElementById(id).innerHTML = sources.map(s => `
    <a class="source-card" href="${s.url}" target="_blank" rel="noopener">
      <div class="source-name">🔗 ${s.name}</div>
      <div class="source-desc">${s.description}</div>
      <div class="source-use">💡 ${s.use_case}</div>
    </a>
  `).join('');
}

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  loadParties();
  runSearch();
});

async function loadParties() {
  try {
    const res = await fetch('/api/parties');
    const data = await res.json();
    const compSel = document.getElementById('filter-complainant');
    const respSel = document.getElementById('filter-respondent');
    if (compSel) {
      data.complainants.forEach(p => {
        const o = document.createElement('option');
        o.value = p; o.textContent = p;
        compSel.appendChild(o);
      });
    }
    if (respSel) {
      data.respondents.forEach(p => {
        const o = document.createElement('option');
        o.value = p; o.textContent = p;
        respSel.appendChild(o);
      });
    }
  } catch(e) { console.error('loadParties error:', e); }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype='text/html')

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found", "path": request.path}), 404
    return Response(INDEX_HTML, mimetype='text/html')

@app.route("/api/disputes", methods=["GET"])
def get_disputes():
    q = request.args.get("q", "").lower()
    year = request.args.get("year", "")
    agreement = request.args.get("agreement", "").lower()
    sector = request.args.get("sector", "").lower()
    complainant = request.args.get("complainant", "").lower()
    respondent = request.args.get("respondent", "").lower()
    status = request.args.get("status", "").lower()
    saudi_relevance = request.args.get("saudi_relevance", "")
    logic = request.args.get("logic", "AND").upper()
    source_filter = request.args.get("source", "all")  # all | pdf | curated
    page_num = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    # Source filter
    if source_filter == "pdf":
        pool = WTO_PDF_DISPUTES
    elif source_filter == "curated":
        pool = WTO_SAUDI_CASES
    else:
        pool = WTO_ALL_DISPUTES

    results = []
    for d in pool:
        filters = []
        if q:
            text = " ".join([
                d.get("title",""), d.get("subject",""), d.get("sector",""),
                d.get("summary_en",""), d.get("complainant",""), d.get("respondent",""),
                " ".join(d.get("keywords",[])), " ".join(d.get("agreements",[]))
            ]).lower()
            filters.append(q in text)
        if year:
            filters.append(str(d.get("year","")) == year)
        if agreement:
            filters.append(any(agreement in a.lower() for a in d.get("agreements",[])))
        if sector:
            filters.append(sector in d.get("sector","").lower())
        if complainant:
            filters.append(complainant in d.get("complainant","").lower())
        if respondent:
            filters.append(respondent in d.get("respondent","").lower())
        if status:
            filters.append(status in d.get("stage", d.get("status","")).lower())
        if saudi_relevance:
            filters.append(d.get("saudi_relevance","") == saudi_relevance.upper())

        if not filters:
            results.append(d)
        elif logic == "OR":
            if any(filters): results.append(d)
        else:
            if all(filters): results.append(d)

    total = len(results)
    # Pagination
    start = (page_num - 1) * per_page
    paginated = results[start:start + per_page]

    return jsonify({
        "total": total,
        "page": page_num,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "disputes": paginated,
        "source_counts": {
            "all": len(WTO_ALL_DISPUTES),
            "pdf": len(WTO_PDF_DISPUTES),
            "curated": len(WTO_SAUDI_CASES)
        }
    })

@app.route("/api/disputes/<ds_number>", methods=["GET"])
def get_dispute(ds_number):
    for d in WTO_ALL_DISPUTES:
        if d["ds_number"].upper() == ds_number.upper():
            return jsonify(d)
    return jsonify({"error": "Dispute not found"}), 404

@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(build_stats())

@app.route("/api/saudi-watch", methods=["GET"])
def saudi_watch():
    saudi_cases = [
        d for d in WTO_ALL_DISPUTES
        if d.get("complainant","") == "Saudi Arabia"
        or d.get("respondent","") == "Saudi Arabia"
        or "Saudi Arabia" in str(d.get("third_parties",[]))
        or d.get("saudi_relevance") in ["HIGH", "MEDIUM"]
    ]
    saudi_cases.sort(key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("saudi_relevance","LOW"),3))
    return jsonify({"total": len(saudi_cases), "disputes": saudi_cases})

@app.route("/api/pdf-disputes", methods=["GET"])
def get_pdf_disputes():
    """Return only PDF-sourced disputes (1995-2022 official publication)"""
    page_num = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    total = len(WTO_PDF_DISPUTES)
    start = (page_num - 1) * per_page
    return jsonify({
        "total": total,
        "page": page_num,
        "disputes": WTO_PDF_DISPUTES[start:start + per_page],
        "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"
    })

@app.route("/api/ai/analyze", methods=["POST"])
def ai_analyze():
    if not ANTHROPIC_API_KEY or not ANTHROPIC_AVAILABLE:
        return jsonify({"error": "AI غير مفعّل — أضف ANTHROPIC_API_KEY في إعدادات Render", "detail": "Set ANTHROPIC_API_KEY in Render environment variables"}), 503
    data = request.get_json()
    ds_number = data.get("ds_number", "")
    question = data.get("question", "")
    language = data.get("language", "ar")

    dispute = None
    for d in WTO_ALL_DISPUTES:
        if d["ds_number"].upper() == ds_number.upper():
            dispute = d; break
    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    lang_instruction = "أجب باللغة العربية" if language == "ar" else "Respond in English"
    prompt = f"""You are a Senior WTO Legal Advisor.

Dispute: {dispute['ds_number']} — {dispute['title']}
Complainant: {dispute.get('complainant','')}
Respondent: {dispute.get('respondent','')}
Agreements: {', '.join(dispute.get('agreements',[]))}
Stage: {dispute.get('stage', dispute.get('status',''))}
Sector: {dispute.get('sector','')}
Saudi Relevance: {dispute.get('saudi_relevance','')}
Saudi Impact: {dispute.get('saudi_impact','')}
Summary: {dispute.get('summary_en','')}

Question: {question if question else 'Provide a comprehensive legal analysis including: key legal issues, applicable WTO articles, procedural stage, strategic implications for Saudi Arabia, and similar precedent cases.'}

{lang_instruction}. Structure your response with clear sections. Cite specific WTO articles."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"ds_number": ds_number, "analysis": message.content[0].text, "language": language, "dispute": dispute})

@app.route("/api/ai/compare", methods=["POST"])
def ai_compare():
    if not ANTHROPIC_API_KEY or not ANTHROPIC_AVAILABLE:
        return jsonify({"error": "AI غير مفعّل — أضف ANTHROPIC_API_KEY في إعدادات Render", "detail": "Set ANTHROPIC_API_KEY in Render environment variables"}), 503
    data = request.get_json()
    ds_numbers = data.get("ds_numbers", [])
    language = data.get("language", "ar")
    disputes = [d for d in WTO_ALL_DISPUTES if d["ds_number"] in ds_numbers]
    if len(disputes) < 2:
        return jsonify({"error": "Provide at least 2 valid DS numbers"}), 400

    disputes_text = "\n\n".join([
        f"{d['ds_number']}: {d['title']}\nComplainant: {d.get('complainant','')} vs {d.get('respondent','')}\nAgreements: {', '.join(d.get('agreements',[]))}\nStage: {d.get('stage','')}\nSaudi: {d.get('saudi_relevance','')}"
        for d in disputes
    ])
    lang_instruction = "أجب باللغة العربية" if language == "ar" else "Respond in English"
    prompt = f"""Compare these WTO disputes:\n\n{disputes_text}\n\nProvide: legal similarities/differences, applicable WTO law, Saudi Arabia implications, key precedents.\n{lang_instruction}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"comparison": message.content[0].text, "language": language})

@app.route("/api/ai/memo", methods=["POST"])
def ai_memo():
    if not ANTHROPIC_API_KEY or not ANTHROPIC_AVAILABLE:
        return jsonify({"error": "AI غير مفعّل — أضف ANTHROPIC_API_KEY في إعدادات Render", "detail": "Set ANTHROPIC_API_KEY in Render environment variables"}), 503
    data = request.get_json()
    ds_number = data.get("ds_number", "")
    audience = data.get("audience", "government")
    language = data.get("language", "ar")

    dispute = None
    for d in WTO_ALL_DISPUTES:
        if d["ds_number"].upper() == ds_number.upper():
            dispute = d; break
    if not dispute:
        return jsonify({"error": "Dispute not found"}), 404

    lang_instruction = "اكتب المذكرة باللغة العربية بالكامل" if language == "ar" else "Write the memo entirely in English"
    audience_note = "for a Saudi government ministry official" if audience == "government" else "for a private sector executive"

    prompt = f"""Prepare a professional Executive Legal Memorandum {audience_note}.

Dispute: {dispute['ds_number']} — {dispute['title']}
Parties: {dispute.get('complainant','')} vs {dispute.get('respondent','')}
WTO Agreements: {', '.join(dispute.get('agreements',[]))}
Status: {dispute.get('stage', dispute.get('status',''))}
Saudi Impact: {dispute.get('saudi_impact','')}
Summary: {dispute.get('summary_en','')}

Format with sections: Executive Summary, Background, Key Legal Issues, Saudi Arabia Position, Risk Assessment, Strategic Recommendations, Next Steps.
{lang_instruction}. Professional and concise."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"memo": message.content[0].text, "language": language, "dispute": dispute})

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    if not ANTHROPIC_API_KEY or not ANTHROPIC_AVAILABLE:
        return jsonify({"error": "AI غير مفعّل — أضف ANTHROPIC_API_KEY في إعدادات Render", "detail": "Set ANTHROPIC_API_KEY in Render environment variables"}), 503
    data = request.get_json()
    messages_history = data.get("messages", [])
    system_prompt = f"""You are an elite WTO Legal Advisor specializing in:
- WTO Agreements (GATT, GATS, TRIPS, DSU, SCM, TBT, SPS, Anti-Dumping, Safeguards, Agriculture)
- Saudi Arabian trade law and WTO dispute implications
- GCC trade policies and regional agreements
- Saudi Vision 2030 trade implications
- CBAM and carbon border measures

You have access to {len(WTO_ALL_DISPUTES)} WTO dispute cases (1995-2022) from the official WTO One-Page Case Summaries publication, plus curated Saudi-relevant cases.

Always cite specific WTO articles, dispute numbers (DS###), and official sources.
When asked in Arabic, respond in Arabic. When asked in English, respond in English."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1500,
        system=system_prompt, messages=messages_history
    )
    return jsonify({"response": message.content[0].text})

@app.route("/api/sources", methods=["GET"])
def official_sources():
    return jsonify({
        "wto_official": [
            {"name": "WTO Dispute Settlement Database","url": "https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm","description": "Main WTO dispute settlement portal","use_case": "Browse all WTO disputes"},
            {"name": "WTO Find Dispute Cases","url": "https://www.wto.org/english/tratop_e/dispu_e/find_dispu_cases_e.htm","description": "Advanced search for WTO dispute cases","use_case": "Filter cases by year, agreement, country"},
            {"name": "WTO Documents Online","url": "https://docs.wto.org","description": "Official WTO documents repository","use_case": "Panel Reports, AB Reports, DSB Minutes"},
            {"name": "WTO Data Portal","url": "https://data.wto.org","description": "WTO trade statistics","use_case": "Trade data and tariff analysis"},
            {"name": "WTO API Portal","url": "https://api.wto.org","description": "Official WTO API","use_case": "Programmatic data access"}
        ],
        "monitoring": [
            {"name": "ePing SPS/TBT","url": "https://epingalert.org","description": "Real-time SPS/TBT alerts","use_case": "Monitor measures affecting Saudi exports"},
            {"name": "WTO I-TIP","url": "https://i-tip.wto.org","description": "Trade Intelligence Portal","use_case": "Track trade policy measures"}
        ],
        "saudi_official": [
            {"name": "الهيئة العامة للتجارة الخارجية","url": "https://www.gaft.gov.sa","description": "GAFT Saudi Arabia","use_case": "متابعة سياسات التجارة الخارجية"},
            {"name": "هيئة الخبراء — الأنظمة","url": "https://laws.boe.gov.sa","description": "Saudi Official Regulations","use_case": "مراجعة الأنظمة التجارية السعودية"},
            {"name": "هيئة الزكاة والجمارك","url": "https://www.zatca.gov.sa","description": "ZATCA","use_case": "الرسوم الجمركية والإجراءات الجمركية"}
        ],
        "pdf_publication": {
            "name": "WTO One-Page Case Summaries 1995-2022",
            "url": "https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm",
            "loaded_cases": len(WTO_PDF_DISPUTES),
            "description": "Official WTO publication — all dispute summaries from 1995 to 2022"
        }
    })


@app.route("/api/parties", methods=["GET"])
def get_parties():
    """Return all unique complainants and respondents for dropdowns"""
    bad = {'2.', 'AGREEMENT', 'N/A', '', 'غير محدد', 'Respondent', '1.'}
    complainants = set()
    respondents = set()
    for d in WTO_ALL_DISPUTES:
        for c in d.get('complainant', '').split(','):
            c = c.strip()
            if c and c not in bad and len(c) > 2:
                complainants.add(c)
        r = d.get('respondent', '').strip()
        if r and r not in bad and len(r) > 2:
            respondents.add(r)
    all_parties = sorted(complainants | respondents)
    return jsonify({
        "complainants": sorted(complainants),
        "respondents": sorted(respondents),
        "all": all_parties
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "platform": "WTO Dispute Intelligence Platform",
        "version": "2.0.0",
        "total_disputes": len(WTO_ALL_DISPUTES),
        "pdf_disputes": len(WTO_PDF_DISPUTES),
        "saudi_curated": len(WTO_SAUDI_CASES),
        "ai_enabled": bool(ANTHROPIC_API_KEY),
        "data_sources": [
            "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)",
            "WTO Saudi-Relevant Cases (Curated Dataset)"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "detail": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(e)}), 500
    return Response(INDEX_HTML, mimetype="text/html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
