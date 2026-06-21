"""
WTO Dispute Intelligence Platform v3.0
========================================
Backend: Flask + MCP Layer + Anthropic AI
Datasets: WTO Official Publication 1995-2022 + Saudi Curated Cases
MCP Server: WTO Dispute Settlement MCP (Read-Only)
"""

import os, json, re
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

app = Flask(__name__, template_folder=".", static_folder=".")
CORS(app)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")



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


WTO_PDF_DISPUTES = [{"ds_number": "DS2", "title": "US – GASOLINE", "complainant": "Brazil, Venezuela", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. III and XX"], "articles": [], "subject": "The “Gasoline Rule” under the US Clean Air Act that set out the rules for establishing baseline figures for gasoline sold on the US market (different methods for domestic and imported gasoline), with ", "sector": "Energy & Environment", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Energy & Environment السعودي", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure treated imported gasoline “less favourably” than domestic gasoline in violation of Art. III:4, as imported gasoline effectively experienced less favourable sales conditions than those afforded to domestic gasoline. In particular, under the regulation, importers had to adapt to an average standard, i.e. “statutory baseline”, that had no connection to the particular gasoline imported, while refiners of domestic gasoline had only to meet a standard linked to their own product in 1990, i.e. individual refinery baseline. • GATT Art. XX(g) (general exceptions – exhaustible natural resources): In respect of the US defence under Art. XX(g), the Appellate Body modified the Panel's reasoning and found that the measure was “related to” (i.e. “primarily aimed at”) the “conservation of exhaustible natural resources” and thus fell within the scope of Art. XX(g). However, the measure was still not", "keywords": ["energy & environment", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS8", "title": "JAPAN – ALCOHOLIC BEVERAGES II", "complainant": "Canada, European Communities, United States", "respondent": "Japan", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Japanese Liquor Tax Law that established a system of internal taxes applicable to all liquors at different tax rates depending on which category they fell within. The tax law at issue taxed shochu at ", "sector": "Other", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel's finding that vodka was taxed in excess of shochu, in violation of Art. III:2, first sentence, accepting the Panel's interpretation that Art. III:2, first sentence requires an examination of the conformity of an internal tax measures by determining two elements: (i) whether the taxed imported and domestic products are like; and (ii) whether the taxes applied to the imported products are in excess of those applied to the like domestic products. • GATT Art. III:2 (national treatment – taxes and charge), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's finding that shochu and whisky, brandy, rum, gin, genever, and liqueurs were not similarly taxed so as to afford protection to domestic production, in violation of Art. III:2, second sentence. Modifying some of the Panel's reasoning, the Appellate Body clarifi", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS18", "title": "AUSTRALIA – SALMON", "complainant": "Canada", "respondent": "Australia", "third_parties": [], "agreements": ["SPS Arts. 5.1, 5.5 and 5.6"], "articles": [], "subject": "Australia's import prohibition of certain salmon from Canada.", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 5.1 (risk assessment): The Appellate Body, although reversing the Panel's finding because the Panel had examined the wrong measures (i.e. heat-treatment requirement), still found that the correct measure at issue – Australia's import prohibition – violated Art. 5.1 (and, by implication, Art. 2.2) because it was not based on a “risk assessment” requirement under Art. 5.1. • SPS Art. 5.5 (prohibition on discrimination and disguised restriction on international trade): The Appellate Body upheld the Panel's finding that the import prohibition violated Art. 5.5 (and, by implication Art. 2.3) as “arbitrary or unjustifiable” levels of protection were applied to several different yet comparable situations so as to result in “discrimination or a disguised restriction” (i.e. more strict restriction) on imports of salmon, compared to imports of other fish and fish products such as herring and finfish. • SPS Art. 5.6 (appropriate level of protection): The Appellate Body reversed the Pan", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS22", "title": "BRAZIL – DESICCATED COCONUT", "complainant": "Philippines", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I, II and VI"], "articles": [], "subject": "A countervailing duty Brazil imposed on 18 August 1995 based on an investigation initiated on 21 June 1994.", "sector": "Agriculture & Food", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Arts. I (most-favoured-nation treatment), II (schedules of concessions) and VI (anti-dumping and countervailing duties): The Appellate Body upheld the Panel's finding that GATT Arts. I, II and VI did not apply to the Brazilian countervailing duty measure at issue because it was based on an investigation initiated prior to 1 January 1995, the date that the WTO Agreement came into effect for Brazil. Specifically, the Panel found: (i) the subsidy rules in the GATT cannot apply independently of the ASCM; and (ii) non-application of the ASCM renders the subsidy rules in the GATT non-applicable. As for GATT Arts. I and II, they did not apply to this dispute because the claims under these provisions derived from the claims of inconsistency with Art. VI. • AA Art. 13 (due restraint): The Panel found that the exemption for countervailing duties contained in AA Art. 13 did not apply to a dispute based on a countervailing duty investigation initiated prior to the date the WTO Agreement cam", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS24", "title": "US – UNDERWEAR", "complainant": "Costa Rica", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6", "GATT Art. X:2"], "articles": [], "subject": "Quantitative import restriction imposed by the United States, as a transitional safeguard measure under ATC Art. 6.", "sector": "Safeguards", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6.10 (transitional safeguard measures – prospective application): The Appellate Body reversed the Panel's finding and concluded that in the absence of express authorization, the plain language of Art. 6.10 creates a presumption that a measure may be applied only prospectively, and thus may not be backdated so as to apply as of the date of publication of the importing Member's request for consultation. • ATC Art. 6.2 (transitional safeguard measures – serious damage and causation): The Panel refrained from making a finding on whether the United States demonstrated “serious damage” within the meaning of Art. 6.2, stating that ATC Art. 6.3 does not provide sufficient and exclusive guidance in this case. However, the Panel found that the United States had not demonstrated actual threat of serious damage, and therefore had violated Art. 6. The Panel also found that the United States failed to comply with its obligation to examine causality under Art. 6.2. • GATT Art. X:2 (trade r", "keywords": ["safeguards", "ATC", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS26", "title": "EC – HORMONES", "complainant": "United States, Canada", "respondent": "European Communities", "third_parties": [], "agreements": ["SPS Arts. 3 and 5"], "articles": [], "subject": "EC prohibition on the placing on the market and the importation of meat and meat products treated with certain hormones.", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 3.1 (international standards): The Appellate Body rejected the Panel's interpretation and said that the requirement that SPS measures be “based on” international standards, guidelines or recommendations under Art. 3.1 does not mean that SPS measures must “conform to” such standards. • Relationship between SPS Arts. 3.1, 3.2 and 3.3 (harmonization): The Appellate Body rejected the Panel's interpretation that Art. 3.3 is the exception to Arts. 3.1 and 3.2 assimilated together and found that Arts. 3.1, 3.2 and 3.3 apply together, each addressing a separate situation. Accordingly, it reversed the Panel's finding that the burden of proof for the violation under Art. 3.3, as a provision providing the exception, shifts to the responding party. • SPS Art. 5.1 (risk assessment): While upholding the Panel's ultimate conclusion that the EC measure violated Art. 5.1 (and thus Art. 3.3) because it was not based on a risk assessment, the Appellate Body reversed the Panel's interpretation,", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS27", "title": "EC – BANANAS III (ARTICLE 21.5 – ECUADOR II)", "complainant": "United States, Ecuador", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. I, II 2 and XIII", "DSU Art. 21.5"], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2008, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2008", "summary_ar": "", "summary_en": "• GATT Art. XIII (non-discriminatory administration of quantitative restrictions): In the case initiated by Ecuador, the Appellate Body upheld the Panel's finding that, to the extent that the European Communities argued that it had implemented a suggestion pursuant to DSU Art. 19.1, the Panel was not prevented from conducting the assessment requested by Ecuador under DSU Art. 21.5. In both cases, the Appellate Body upheld, albeit for different reasons, the Panel's finding that the EC bananas import regime, in particular its duty-free tariff quota reserved for ACP countries, was inconsistent with Arts. XIII:1 and XIII:2. • GATT Art II (schedules of concessions): The Appellate Body reversed the Panel's finding that the waiver approved in November 2001 by the Ministerial Conference in Doha constituted a subsequent agreement between the parties extending the tariff quota concession for bananas listed in the European Communities' Schedule of Concessions beyond 31 December 2002, until the re", "keywords": ["agriculture & food", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS31", "title": "CANADA – PERIODICALS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. III, XI and XX"], "articles": [], "subject": "(i) Tariff Code 9958, which prohibited the importation into Canada of any periodical that was a “special edition” 2; (ii) the Excise Tax Act, which imposed, in respect of each split-run edition3 of a ", "sector": "Anti-Dumping", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions) and Art. XX(d) (exceptions – necessary to secure compliance with laws): The Panel found that Tariff Code 9958, which prohibited the importation of certain periodicals, violated Art. XI, and was not justified under Art. XX(d) because it could not be regarded as a measure to secure compliance with Canada's Income Tax Act. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Appellate Body reversed the Panel's finding that imported split-run periodicals and domestic non-split run periodicals were “like products” (Art. III:2, first sentence). The Appellate Body concluded that the Excise Tax Act was inconsistent with Art. III:2, second sentence because (i) imported split-run periodicals were “directly competitive or substitutable” with domestic non-split-run periodicals; (ii) imported and domestic products were not similarly taxed; and (iii) the tax was applied so as to afford protection to dome", "keywords": ["anti-dumping", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS33", "title": "US – WOOL SHIRTS AND BLOUSES", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ATC Arts. 6 and 2.4"], "articles": [], "subject": "Temporary safeguard measure imposed by the United States in the form of a quota on certain imports from India.", "sector": "Safeguards", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6 (transitional safeguard measures): The Panel found that the United States violated Arts. 6.2 and 6.3 because it failed to meet the causation and serious damage (and threat of serious damage) requirements therein when imposing its transitional safeguard measure, in particular, by not examining the data relevant to the “woven wool shirts and blouses industry”, as opposed to the “woven shirts and blouses industry in general”. The Panel also considered the list of industry impact factors in Art. 6.3 to be a mandatory list: an investigating authority must demonstrate that it considered the relevance or otherwise of each of the listed items in Art. 6.3. Moreover, the Panel stated that under Art. 6.3, “some consideration and a relevant and adequate explanation have to be provided of how the facts as a whole support the conclusion that the termination is consistent with the requirements of the ATC”. • ATC Art. 2.4 (prohibition on new restrictions): The Panel found that, by violati", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS34", "title": "TURKEY – TEXTILES", "complainant": "India", "respondent": "Turkey", "third_parties": [], "agreements": ["GATT Arts. XI, XIII and XXIV", "ATC Art. 2.4"], "articles": [], "subject": "Turkey's quantitative import restrictions pursuant to the Turkey-EC customs union.", "sector": "Textiles", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Arts. XI (prohibition on quantitative restrictions) and XIII (non-discriminatory administration of quantitative restrictions): The Panel found that the quantitative restrictions at issue were inconsistent with Arts. XI and XIII. (Turkey did not deny this.) • ATC Art. 2.4 (prohibition on new restrictions): The Panel found that Turkey's measures were new restrictions, that did not exist at the time of the entry into force of the ATC, and, thus, were prohibited by Art. 2.4. • GATT Art. XXIV (regional trade agreements): The Appellate Body agreed with the Panel's ultimate conclusion that Turkey's measures were not justified under Art. XXIV because there were alternatives available to Turkey that would have met the requirements of Art. XXIV:8(a), which were necessary to form the customs union, other than the adoption of the quantitative restrictions. The Appellate Body, therefore, modified the Panel's legal reasoning and concluded that to determine whether a measure found inconsistent", "keywords": ["textiles", "GATT", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS44", "title": "JAPAN – FILM", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["GATT Arts. XXIII:1(b), III:4 and X:1"], "articles": [], "subject": "Actions by Japan affecting the distribution, offering for sale, and internal sale of imported consumer photographic film and paper, in particular, (i) distribution measures; (ii) restrictions on large", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XXIII:1(b) (non-violation claim): The Panel found that the United States failed to demonstrate that the measures at issue nullified or impaired benefits accruing to the United States within the meaning of Art. XXIII:1(b). The Panel considered that a complaining party must demonstrate three elements under Art. XXIII:1(b): (i) application of a measure by a WTO Member; (ii) a benefit accruing under the relevant agreement: and (iii) nullification or impairment of the benefit as the result of the application of the measure. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the distribution measures were generally origin-neutral and did not have a disparate impact on imported film or paper. The Panel therefore found that the United States had not proved that the distribution measures were inconsistent with Art. III:4. • GATT Art. X:1 (trade regulations – prompt publication): The Panel considered that the publication requirement in Art. X", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS46", "title": "BRAZIL – AIRCRAFT (ARTICLE 21.5 – CANADA)", "complainant": "Canada", "respondent": "Brazil", "third_parties": [], "agreements": ["ASCM Art. 4.7 and Annex I, item (k)"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2000, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2000", "summary_ar": "", "summary_en": "• ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): The Appellate Body upheld the Panel's findings that Brazil was in violation of Art. 4.7 as it had not withdrawn the export subsidies for regional aircraft within 90 days of the adoption of the original panel and Appellate Body reports. The Appellate Body stated that Brazil's argument that it was continuing to make payments under letters of commitment (private contractual obligations under domestic law), which had been made before the expiry of the 90‑day period of implementation, was not an adequate defence against the implementation of DSB recommendations. • ASCM Annex I, Illustrative List of Export Subsidies, item (k): The Appellate Body upheld the Panel's conclusion and found that Brazil had failed to demonstrate that the PROEX payments were not used to secure a material advantage in the field of export credit terms within the meaning of item (k) because Brazil had not identified an appropriate “market benchmark” for", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS50", "title": "INDIA – PATENTS (US)", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Art. 70.8 and 70.9"], "articles": [], "subject": "(i) India's “mailbox rule” – under which patent applications for pharmaceutical and agricultural chemical products could be filed; and (ii) the mechanism for granting exclusive marketing rights to suc", "sector": "Intellectual Property", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Appellate Body upheld the Panel's finding that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Appellate Body found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the administrative instructions could be rejected by the court under the contradictory mandatory provisions of the existing Indian laws: the Patents Act of 1970. • TRIPS Art. 70.9 (exclusive marketing rights): The Appellate Body agreed with the Panel that there was no mechanism in place in India for the grant of exclusive marketing rights for the products covered by Art. 70.8(a) and thus Art. 70.9 was violated.", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS54", "title": "INDONESIA – AUTOS", "complainant": "European Communities, United States, Japan", "respondent": "Indonesia", "third_parties": [], "agreements": ["TRIMs Art. 2.1", "GATT Arts. I:1 and III:2", "ASCM Arts. 5(c), 6, 27.9 and 28"], "articles": [], "subject": "(i) “The 1993 Programme” that provided import duty reductions or exemptions on imports of automotive parts based on the local content percent; and (ii) “The 1996 National Car Programme” that provided ", "sector": "Subsidies & Anti-Subsidy", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIMs Agreement Art. 2.1 (local content requirement): 2 The Panel found the 1993 Programme to be in violation of Art. 2.1 because (i) the measure was a “trade-related investment”3 measure; and (ii) the measure, as a local content requirement, fell within para. 1 of the Illustrative List of TRIMs in the Annex to the TRIMs Agreement, which sets out trade-related investment measures that are inconsistent with national treatment obligation under GATT Art. III:4. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Panel found that the sales tax benefits under the measures violated both Art. III:2, first and second sentences. The Panel noted that under the Indonesian car programmes, an imported motor vehicle would be taxed at a higher rate than a like domestic vehicle in violation of Art. III:2, first sentence, and also, any imported vehicle would not be taxed similarly to a directly competitive or substitutable domestic car due to these Indonesian c", "keywords": ["subsidies & anti-subsidy", "TRIMs", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS56", "title": "ARGENTINA – TEXTILES AND APPAREL", "complainant": "United States", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. II and VIII"], "articles": [], "subject": "(i) Argentina's system of minimum specific import duties, known as “DIEM”, on textiles and apparel (under which textiles and apparel were subject to either a 35 per cent ad valorem duty or a minimum s", "sector": "Textiles", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II (schedules of concessions): The Appellate Body found Argentina's measure was, in fact, inconsistent with Art. II:1(b). It held that “the application of a type of duty different from the type provided for in a Member's Schedule is inconsistent with GATT Art. II:1(b), first sentence, to the extent that it results in ordinary customs duties being levied in excess of those provided for in that Member's Schedule.” In this case, the Appellate Body concluded that “the structure and design of the Argentine system is such that for any DIEM ... the possibility remains that there is a ‘break-even’ price below which the ad valorem equivalent of the customs duty collected is in excess of the bound ad valorem rate of 35 per cent.” • GATT Art. VIII (fees and formalities): The Appellate Body upheld the Panel's findings that the statistical tax on imports violated Argentina's obligations under Art. VIII:1(a) “to the extent it results in charges being levied in excess of the approximate c", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS58", "title": "US – SHRIMP", "complainant": "India, Malaysia, Pakistan, Thailand", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. XI and XX"], "articles": [], "subject": "US import prohibition of shrimp and shrimp products from non-certified countries (i.e. countries that had not used a certain net in catching shrimp).", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel found that the US prohibition, based on Section 609, on imported shrimp and shrimp products violated Art. XI. The United States apparently conceded the measure's violation of Art. XI because it did not put forward any defending arguments in this regard. • GATT Art. XX(g) (general exceptions – exhaustible natural resources): The Appellate Body held that although the US import ban was related to the conservation of exhaustible natural resources and, thus, covered by an Art. XX(g) exception, it could not be justified under Art. XX because the ban constituted “arbitrary and unjustifiable” discrimination under the chapeau of Art. XX. In reaching this conclusion, the Appellate Body reasoned, inter alia, that in its application the measure was “unjustifiably” discriminatory because of its intended and actual coercive effect on the specific policy decisions made by foreign governments that were Members of the WTO. The measure", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS60", "title": "GUATEMALA – CEMENT I", "complainant": "Mexico", "respondent": "Guatemala", "third_parties": [], "agreements": ["DSU Art. 6.2", "ADA Art. 17.4 (Art. 5)"], "articles": [], "subject": "Guatemala's anti-dumping investigation (both the initiation and various decisions and conduct of the Ministry).", "sector": "Anti-Dumping", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1998", "summary_ar": "", "summary_en": "• DSU Art. 6.2 and ADA Art. 17.4 (requirements of panel request): The Appellate Body, reversing the Panel, concluded that Mexico had failed to identify in its panel request the “specific measures at issue” in accordance with DSU Art. 6.2 and ADA Art. 17.4, i.e. one of the three measures to be specified in a dispute involving anti-dumping investigations: (i) a definitive antidumping duty, (ii) the acceptance of a price undertaking, or (iii) a provisional anti-dumping measure. According to the Appellate Body, the special dispute settlement rules in the ADA and the DSU provisions together create a “comprehensive, integrated dispute settlement system” rather than the former replacing the more general rules in the DSU as the Panel had erroneously found. The Appellate Body rejected the Panel's reasoning that the term “measure” under DSU Art. 6.2 should be interpreted broadly, and clarified that both identification of “measure” and identification of the alleged “violations” are separately req", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS62", "title": "EC – COMPUTER EQUIPMENT", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II:1"], "articles": [], "subject": "The European Communities' application of tariffs on local area networks: (LAN) equipment and multimedia personal computers (PCs) in excess of those provided for in the EC Schedules through changes in ", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedule of concessions – LAN): The Appellate Body reversed the Panel's finding of a violation by the European Communities of Art. II:1 with respect to LAN equipment on the basis of the Panel's erroneous legal reasoning and consideration of only selective evidence. In this regard the Appellate Body rejected the Panel's finding that a tariff concession in the Schedule can be interpreted in light of an exporting Member's “legitimate expectations” – a concept relevant to a nonviolation complainant under GATT Art. XXIII:1(b) – in the context of a violation complaint. Rather, the Appellate Body found that a tariff concession provided for in the Member's Schedule should be interpreted according to the general rules of treaty interpretation set out in Arts. 31 and 32 of the VCLT2; Moreover, the Appellate Body said that the Panel should have further examined the following: the Harmonized System and its Explanatory Notes as context in interpretation of the terms of the Schedul", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS69", "title": "EC – POULTRY", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. XIII, X"], "articles": [], "subject": "European Communities' tariff rate quota (TRQ) system incorporated into EC Schedule LXXX with respect to frozen poultry and the European Communities' licensing requirements for importers of the product", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XIII:2 (non-discriminatory administration of quantitative restrictions): The Appellate Body upheld the Panel's finding that the TRQ must be administered on a non-discriminatory basis – as opposed to it being awarded exclusively to Brazil – based on the text of the EC Schedule LXXX and pursuant to Art. XIII, and thus, the European Communities had acted consistently with its WTO obligations. The Appellate Body also upheld the Panel's finding that, even when a TRQ is the result of an Art. XXVIII compensation negotiation, it must be administered in a non-discriminatory manner (total imports, including those from non-Members). The Appellate Body also agreed with the Panel that TRQ shares must be calculated on the basis of “total imports”, including imports coming from non-Members, and thus, the European Communities acted consistently with Art. XIII:2 by including imports from non-Members in its TRQ calculation. • GATT Art. X (publication and administration of trade regulation): ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS70", "title": "CANADA – AIRCRAFT", "complainant": "Brazil", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1 and 4.7"], "articles": [], "subject": "Canadian measures providing various forms of financial support to the domestic civil aircraft industry.", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (definition of a subsidy): The Panel found that a “financial contribution” confers a “benefit” and constitutes a subsidy under Art. 1 when provided on terms more advantageous than those otherwise available to the recipient on the market. The Appellate Body, while upholding this finding, concluded that the word “conferred”, in conjunction with “thereby”, calls for an inquiry into what was conferred on the recipient, not an inquiry into the cost to the government as argued by Canada. • ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): The Appellate Body upheld the Panel's finding that contingency exists if there is a relationship of conditionality or dependence between the grant of the subsidy and the anticipated exportation or export earnings. • Examination of Canada's individual measures (as such/as applied distinction for discretionary and mandatory measures): The Panel concluded that the EDC programme as such was discretionary legislation and, upon examinati", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS75", "title": "KOREA – ALCOHOLIC BEVERAGES", "complainant": "European Communities, United States", "respondent": "Korea", "third_parties": [], "agreements": ["GATT Art. III:2, second sentence"], "articles": [], "subject": "Korea's tax regime for alcoholic beverages, which imposed different tax rates for various categories of distilled spirits.", "sector": "Other", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's conclusion that the Korean tax measures at issue were inconsistent with Art. III:2, second sentence: More specifically, the Appellate Body upheld the Panel's findings that the products at issue were “directly competitive or substitutable” within the meaning of Art. III:2, second sentence and that Korea's tax measures on alcoholic beverages were applied “so as to afford protection” to domestic production within the meaning of Art. III:2, second sentence. On the question of the interpretation and application of the term “directly competitive or substitutable product”, the Appellate Body upheld the Panel's approach: (i) the Panel correctly considered evidence of “present direct competition”, not the future evolution of the market, by referring to the potential for the products to compete in a market free of protection because i", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS76", "title": "JAPAN – AGRICULTURAL PRODUCTS II", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7, 5.6 and 5.1"], "articles": [], "subject": "Varietal testing requirement (Japan's Plant Protection Law), under which the import of certain plants was prohibited because of the possibility of their becoming potential hosts of codling moth.", "sector": "Agriculture & Food", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that Japan's varietal testing requirement was maintained without sufficient scientific evidence in violation of Art. 2.2.3 • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the varietal testing requirement was not justified under Art. 5.7 because Japan did not meet all the requirements for the adoption and maintenance of a provisional SPS measure as set out in Art. 5.7. • SPS Art. 5.6 (appropriate level of protection – alternative measures): Having found that the United States, as a complainant, did not claim and, therefore, could not have established a prima facie case of Japan's inconsistency with the existence of an alternative measure (determination of sorption levels) under Art. 5.6, the Appellate Body reversed the Panel's finding that Japan acted inconsistently with Art. 5.6. Then, as to the alternative measure proposed by the United States – i.e. ", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS79", "title": "INDIA – PATENTS (EC)", "complainant": "European Communities", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Arts. 70.8 and 70.9"], "articles": [], "subject": "(i) The insufficiency of the legal regime – India's “mailbox rule” – under which patent applications for pharmaceutical and agricultural chemical products could be filed; and (ii) the lack of a mechan", "sector": "Intellectual Property", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Panel held that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Panel found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the current administrative instructions could be rejected by the court under the contradictory mandatory provisions of the pertinent Indian law – the Patents Act of 1970. • TRIPS Art. 70.9 (exclusive marketing rights): The Panel found that there was no mechanism in place in India for the grant of “exclusive marketing rights” for pharmaceutical and agricultural chemical products and thus Art. 70.9 had been violated. 1 India – Patent Protection for Pharmaceutical and Agricultural Chemical Products (complaint by the European Communi", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS87", "title": "CHILE – ALCOHOLIC BEVERAGES", "complainant": "European Communities", "respondent": "Chile", "third_parties": [], "agreements": ["GATT Art. III:2"], "articles": [], "subject": "Chile's tax measures that imposed an excise tax at different rates – depending on the type of product (pisco, whisky, etc.) under the “Transitional System” and according to the degree of alcohol conte", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's finding that Chile's new tax regime for alcoholic beverages violated the national treatment principle under Art. III:2, second sentence. (Chile's appeal was only in regard to the new regime.) The Panel found both Chile's transitional and new tax regimes inconsistent with Art. III:2, second sentence. (“not similarly taxed”): The Appellate Body agreed with the Panel that imported distilled spirits and Chilean pisco, as directly competitive and substitutable products, were not similarly taxed since the tax burden (47 per cent) on most of imported products (95 per cent of imports) would be heavier than the tax burden (27 per cent) on most of the domestic products (75 per cent of domestic production). The Appellate Body took the view that the relevant comparison between imported and domestic products had to be made based on a com", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS99", "title": "US – DRAMS", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 11, 2.2, 6.6 and 5.8"], "articles": [], "subject": "United States Department of Commerce (USDOC) regulation (namely, the “three zeroes” rules)2, both as applied in the DRAMS third administrative review at issue and as such, and other aspects of the thi", "sector": "Anti-Dumping", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ADA Art. 11.2 (review of anti-dumping duties – the “likely” standard): The Panel found for Korea and held that the “not likely” standard in the US regulation (as quoted in footnote 2 below), as such, is inconsistent with Art. 11.2 (“likely” standard) because a failure to find that an exporter is “not likely” to dump does not necessarily lead to the conclusion that this exporter is therefore “likely” to dump. The Panel considered that because there are situations where the not “not likely” standard is satisfied but the “likely” standard is not, the “not likely” criterion fails to provide a “demonstrable basis for consistently and reliably determining that the likelihood criterion is satisfied”. The Panel also found that because the final results of the third administrative review in the DRAMS case were based on a USDOC determination under that regulation, those results, as applied, were inconsistent with Art. 11.2 as well. • ADA Art. 2.2.1.1 (dumping determination – acceptance of data", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS103", "title": "CANADA – DAIRY (ARTICLE 21.5 – NEW ZEALAND AND US)", "complainant": "New Zealand, United States", "respondent": "Canada", "third_parties": [], "agreements": [], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2001, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2001", "summary_ar": "", "summary_en": "• AA Art. 9.1(c) (export subsidies – payments financed by virtue of governmental action): On the question of whether the Canadian measures were “payments on the export of an agricultural product that are financed by virtue of governmental action” and thus constituted a subsidy under Art. 9.1(c) (which was made in excess of its export subsidy and quantity commitments in violation of Arts. 3.3 and 8 thereof), the Appellate Body reversed the Panel's legal findings as follows. (The Appellate Body, however, did not complete the analyses based on the correct legal standard.)3 (“payments”) The Appellate Body held first that neither prices for milk destined for the domestic market nor world market prices could serve as the appropriate basis for determining whether prices charged for export sales constituted a “payment” within the meaning of Art. 9.1 (c). The Appellate Body, while holding that the “average total cost of production” was the appropriate standard for determining whether export sal", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS108", "title": "US – FSC (ARTICLE 21.5 – EC II)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 4.7"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2006, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2006", "summary_ar": "", "summary_en": "• ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): Having concluded that the “recommendation under Art. 4.7 remains in effect until the Member concerned has fulfilled its obligation by fully withdrawing the prohibited subsidy”, the Appellate Body upheld the Panel's finding that “to the extent that the United States, by enacting Section 101 of the Jobs Act, maintains prohibited FSC and ETI subsidies through the transitional and grandfathering measures, it continues to fail to implement fully the operative DSB recommendations and rulings to withdraw the prohibited subsidies and to bring its measures into conformity with its obligations under the relevant covered agreements.” In this regard, it agreed with the Panel that “the relevant recommendations adopted by the DSB in the original proceedings in 2000, and those in the first and these second Art. 21.5 proceedings, form part of a continuum of events relating to compliance with the recommendations and rulings of the DSB i", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS114", "title": "CANADA – PHARMACEUTICAL PATENTS", "complainant": "European Communities", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 27, 28 and 30"], "articles": [], "subject": "Certain provisions under Canada's Patent Act: (i)”regulatory review provision (Sec. 55.2(1))” 2; and (ii)”stockpiling provision (Sec. 55.2(2))” that allowed general drug manufacturers to override, in ", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "Stockpiling provision • TRIPS Arts. 28.1 (patent owner rights) and 30 (exceptions): (Canada practically conceded that the stockpiling provision violated Art. 28.1, which sets out exclusive rights granted to patent owners.) Concerning Canada's defence under Art. 30, the Panel found that the measure was not justified under Art. 30 because there were no limitations on the quantity of production for stockpiling which resulted in a substantial curtailment of extended market exclusivity, and, thus, was not “limited” as required by Art. 30. Accordingly, the Panel concluded that the stockpiling provision was inconsistent with Art. 28.1 as it constituted a “substantial curtailment of the exclusionary rights” granted to patent holders. Regulatory review provision • TRIPS Arts. 28.1 (patent owner rights) and 30 (exceptions): (Canada also practically conceded on the inconsistency of the provision with Art. 28.1) The Panel found that Canada's regulatory review provision was justified under Art. 30 ", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS122", "title": "THAILAND – H-BEAMS", "complainant": "Poland", "respondent": "Thailand", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 17.6"], "articles": [], "subject": "Thailand's definitive anti-dumping determination.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 5 (initiation of investigation): The Panel rejected Poland's claim that the Thai authorities' initiation of the investigation could not be justified due to the insufficiency of evidence originally contained in the application. The Panel considered that the application need not contain analysis, but only information. The Panel also rejected Poland's claim that Thailand violated Art. 5.5 by failing to provide a written notification of the filing of application for initiation of investigation. The Panel considered that a formal meeting could satisfy the requirement. • ADA Art. 2.2 (dumping determination – constructed normal value): As the Panel found that, (i) for the purpose of calculating a dumping margin under Art. 2.2, Thailand used the narrowest product category that included the like product; and (ii) that no separate reasonability test was required in choosing a profit figure for constructed normal value, the Panel concluded that Thailand had not violated Art. 2.2. • ADA", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS126", "title": "AUSTRALIA – AUTOMOTIVE LEATHER II", "complainant": "United States", "respondent": "Australia", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1(a) and 4.7"], "articles": [], "subject": "Australian government's assistance (“grant contract” ($A 30 million) and “loan contract” ($A 25 million)) to Howe, a wholly-owned subsidiary of Australian Leather Upholstery Pty. Ltd., owned by Austra", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): As for the grant contract, the Panel found that the payments under the grant contract were subsidies prohibited under Art. 3.1(a), on the ground that the payments concerned were in fact “tied to” export performance. In respect of the loan contract, the Panel concluded that the payments under the loan contract did not violate Art. 3.1(a) because there was nothing in the terms of the loan contract itself that suggested a “specific link” to actual or anticipated exportation or export earnings. • ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): The Panel recommended, in accordance with Art. 4.7, that Australia withdraw the prohibited subsidies within a 90-day period, which would run from the date of adoption of the report by the DSB.", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS136", "title": "US – 1916 ACT", "complainant": "European Communities, Japan", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI", "ADA Arts. 1, 4, 5 and 18"], "articles": [], "subject": "United States' Anti-Dumping Act of 1916, which provided for, inter alia, a private right of action, the remedy of treble damages for private complaints and the possibility of criminal penalties in res", "sector": "Anti-Dumping", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. VI and ADA (applicability): The Appellate Body upheld the Panel's finding that GATT Art. VI and the ADA applied to the 1916 Act. Art. VI applies to action taken in response to situations involving dumping and the 1916 Act provided for specific action to be taken in situations that present the constituent elements of dumping within the meaning of that provision. • GATT Art. VI and ADA (substantive violations): 2 The Appellate Body upheld the Panel's findings on the following claims: the 1916 Act was inconsistent with: (i) GATT Art. VI (anti-dumping duties) which, read in conjunction with the ADA, limits the permissible responses to dumping to definitive anti‑dumping duties, provisional measures and price undertakings; (ii) GATT Art. VI:1 (anti-dumping duties – conditions) because it did not require a finding of “material injury”; (iii) ADA Art. 4 (and 5 as well in case of Japan): (definition of domestic industry) because the Act did not require that a complaint be made “on b", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS139", "title": "CANADA – AUTOS", "complainant": "European Communities, Japan", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3 and 4.7", "GATS Arts. I and II", "GATT Arts. I and III"], "articles": [], "subject": "Canada's import duty exemption for imports by certain manufacturers, in conjunction with the Canadian Value Added (CVA) requirements and the production to sales ratio requirements.", "sector": "Services", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. I (most-favoured-nation treatment): The Appellate Body upheld the Panel's finding that the duty exemption was inconsistent with the most-favoured-nation treatment obligation under Art. I:1 on the ground that Art. I:1 covers not only de jure but also de facto discrimination and that the duty exemption at issue in reality was given only to the imports from a small number of countries in which an exporter was affiliated with eligible Canadian manufacturers/importers. The Panel rejected Canada's defence that Art. XXIV allows the duty exemption for NAFTA members (Mexico and the United States), because it found that the exemption was provided to countries other than the United States and Mexico and because the exemption did not apply to all manufacturers from these countries. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the CVA requirements forcing the use of domestic materials to be eligible for tax exemption resulted in “less favo", "keywords": ["services", "ASCM", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS141", "title": "EC – BED LINEN (ARTICLE 21.5 – INDIA)", "complainant": "India", "respondent": "European Communities", "third_parties": [], "agreements": ["ADA Arts. 3 and 15"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2003, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.2 (injury determination – volume of dumped imports): The Appellate Body reversed the Panel's findings on this issue and concluded that the European Communities' consideration of all imports from un-examined producers as dumped for the purposes of the injury analysis was based on a presumption not supported by positive evidence. Therefore, the Appellate Body held that the European Communities acted inconsistently with Arts. 3.1 and 3.2 as it had not determined the “volume of dumped imports” on the basis of “positive evidence” and an “objective assessment”. • ADA Arts. 3.1 and 3.4 (injury determination – injury factors): The Panel rejected India's claim that the European Communities did not have information on the economic factors and indices in Art. 3.4 (i.e. inventories and capacity utilization). The Panel concluded that the European Communities had collected data on these factors and that it did conduct an overall reconsideration and analysis of the facts with re", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS146", "title": "INDIA – AUTOS", "complainant": "European Communities, United States", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. III, XI and XVIII:B", "DSU Art. 19.1"], "articles": [], "subject": "India's (i) indigenization (local content) requirement; and (ii) trade balancing requirement (exports value = imports value) imposed on its automotive sector.2", "sector": "Automotive", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "Indigenization requirement • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel concluded that the measure violated Art. III:4, as the indigenization requirement modified the conditions of competition in the Indian market “to the detriment of imported car parts and components”. Trade balancing requirement • GATT Art. XI:1 (prohibition on quantitative restrictions): Having found that “any form of limitation imposed on, or in relation to importation constitutes a restriction on importation within the meaning of Art. XI”, the Panel found that India's trade balancing requirement, which limited the amount of imports in relation to an export commitment, acted as a restriction on importation within the meaning of Art. XI:1, and thus violated Art. XI:1. The Panel also found that India failed to make a prima facie case that this requirement was justified under the balance-of-payments provisions of Art. XVIII:B. • GATT Art. III:4 (national treatment – domestic laws a", "keywords": ["automotive", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS152", "title": "US – SECTION 301 TRADE ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Art. 23.2(a) and (c)"], "articles": [], "subject": "US legislation (i.e. Sections 301-310 of the Trade Act of 1974) authorizing certain actions by the Office of the United States Trade Representative (USTR), including the suspension or withdrawal of co", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• DSU Art. 23.2(a) (prohibition on unilateral determinations – Section 304): Based on the terms of Art. 23.2(a), the Panel first set out that it is for the WTO, through the DSU process, and not an individual WTO Member, to determine that a measure is inconsistent with WTO obligations. The Panel then concluded that Section 304 was “not inconsistent” with US obligations under Art. 23.2(a) because, while the statutory language of Section 304 in itself constituted a serious threat that unilateral determinations contrary to Art. 23.2(a) might be taken, the United States had (i) lawfully removed this threat by the “aggregate effect of the Statement of Administrative Action ('SAA')” and (ii) made a statement before the Panel that it would render determinations under Section 304 in conformity with its WTO obligations. In this regard, the Panel added the caveat, however, that should the United States repudiate or remove in any way its undertakings contained in the SAA and confirmed in statement", "keywords": ["other", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS155", "title": "ARGENTINA – HIDES AND LEATHER", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. III:2, X, XI and XX"], "articles": [], "subject": "(i) Argentine regulations by which representatives of the Argentine leather tanning industry were present during the customs clearance process for bovine hides export; and (ii) advance tax payments th", "sector": "Other", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2001", "summary_ar": "", "summary_en": "Regulations on export control • GATT Art. XI:1 (prohibition on quantitative restrictions): The Panel rejected the EC claim that the Argentine regulations on export procedures were an export restriction prohibited by Art. XI. The European Communities had failed to meet its burden of proving that the presence of the tanners' representatives during customs procedures, along with the disclosure of information about the slaughterhouses and any possible abuse of this information, was an export restriction under Art. XI:1. • GATT Art. X:3(a) (trade regulations – uniform, impartial and reasonable administration): Having concluded that Art. X:3(a) applied to the measure at issue, as (i) the substance of the measure at issue was “administrative in nature” and did not establish substantive customs rules for enforcement of export laws and (ii) the measure was a law of “general application,” rather than a law applying only to the specific shipments of products, the Panel found that the measure was ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS163", "title": "KOREA – PROCUREMENT", "complainant": "United States", "respondent": "Korea", "third_parties": [], "agreements": ["GPA Arts. I and XXII:2"], "articles": [], "subject": "", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GPA Art. I (scope of Korea's GPA Appendix I commitment): The Panel found, based on the terms of Korea's concessions in its GPA Schedule and the supplementary negotiating history of the Schedule, that the entities allegedly responsible for IIA procurement – i.e. NADG or KAA – were not entities covered by Korea's GPA schedule, and thus concluded that the IIA project was not covered by Korea's commitments under the GPA. • GPA Art. XXII:2 (non-violation nullification or impairment): Regarding the US non-violation claim under GPA Art. XXII:2, which was based on the frustration of reasonably expected benefits from alleged promises made during “negotiations” rather than nullification or impairment of actual concessions made, the Panel considered that the concept of non-violation could be extended to contexts other than the traditional approach. As such, the Panel decided to examine the US claim “within the framework of principles of international law (Art. 48 of the VCLT) which are generall", "keywords": ["other", "GPA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS170", "title": "CANADA – PATENT TERM", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 33 and 70"], "articles": [], "subject": "Canada's Patent Act, Section 45, which provided the length of the patent protection for patents filed before 1 October 1989 (Old Act).2", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• TRIPS Art. 70.1 and 70.2 (protection of existing subject matter): (Art. 70.2) Having found that “a treaty applies to existing rights, even when those rights result from 'acts which occurred' before the treaty entered into force” and Art. 70.2 applies to existing inventions (rights) under Old Act patents whose patents were granted (acts) before the date of entry into force of the TRIPS Agreement, the Appellate Body concluded that Canada was bound by the obligation to provide existing patented inventions with a patent term of not less than 20 years from the filing date as required under Art. 33. (Art. 70.1) The Appellate Body also upheld the Panel's finding that Art. 70.1, limiting the retroactive application of the TRIPS Agreement, did not exclude Old Act patents from the scope of the TRIPS Agreement, as “acts” and the “rights created by such acts” should be distinguished and the limitation under Art. 70.1 applies to acts related to the patent, not rights provided by patent itself. • ", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS176", "title": "US – SECTION 211 APPROPRIATIONS ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["TRIPS Arts. 2, 3, 4, 15, 16 and 42"], "articles": [], "subject": "Section 211 of the US Omnibus Appropriations Act of 1998, prohibiting those having an interest in trademarks/trade names related to certain businesses or assets confiscated by the Cuban government fro", "sector": "Intellectual Property", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "Section 211(a)(1) • TRIPS Art. 15 (trademarks – protectable subject matter) and Art. 2.1 (Paris Convention Art. 6quinquies A(1): As Art. 15.1 embodies a definition of a trademark and sets forth only the eligibility criteria for registration as trademarks (but not an obligation to register “all” eligible trademarks), the Appellate Body found that Section 211(a)(1) was not inconsistent with Art. 15.1, as the regulation concerned “ownership” of a trademark. The Appellate Body also agreed with the Panel that Section 211(a)(1) was not inconsistent with Paris Convention Art. 6quinquies A(1), which addressees only the “form” of a trademark, not ownership. Sections 211(a)(2) and (b) • TRIPS Arts. 16.1 (trademarks – exclusive rights of the owners and limited exceptions) and 42 (civil and administrative procedures and remedies): As there are no rules determining the “owner” of a trademark (i.e. discretion left to individual countries), the Appellate Body found that Section 211(a)(2) and (b) were", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS179", "title": "US – STAINLESS STEEL", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2"], "articles": [], "subject": "Definitive anti-dumping duties imposed by the United States on certain steel imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 2.4.1 (dumping determination – currency conversion): Having found that where the prices being compared (i.e. export price and normal price) were already in the same currency, “currency conversion” was not required and thus not permissible under Art. 2.4.1, the Panel concluded that the United States acted inconsistently with Art. 2.4.1 by making a currency conversion that was not required in the Sheet investigation, but did not act inconsistently with Art. 2.4.1 in the Plate investigation. • ADA Art. 2.4 (dumping determination – unpaid sales): In calculating a “constructed export price”, the Panel found that Members are permitted to make only those adjustments identified in Art. 2.4 (i.e. allowances for costs, including duties and taxes, incurred between importation and resale), and thus concluded that the United States improperly calculated a constructed export price in respect of sales made through an affiliated importer by deducting the unpaid sales (from bankrupted buyer)", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS184", "title": "US – HOT-ROLLED STEEL", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6 and 9"], "articles": [], "subject": "US definitive anti-dumping duties on certain imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 (evidence – facts available): The Appellate Body upheld the Panel's findings that the United States acted inconsistently with Art. 6.8 in applying facts available to exporters, as the United States Department of Commerce (USDOC) had rejected certain information submitted after the deadline without considering whether it was still submitted within a reasonable period of time. The Appellate Body upheld the Panel's finding that the United States acted inconsistently with Art. 6.8 and Annex II when it applied “adverse” facts available to an exporter in respect of certain resale prices by its affiliated company despite the difficulties faced by that exporter in obtaining the requested information and USDOC's reluctance to take any step to assist it. • ADA Art. 9.4 (imposition of anti-dumping duties – “all others” rate): Having found that margins established based in part on facts available are to be excluded in calculating an “all others” rate under Art. 9.4, the Appellate Bo", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS189", "title": "ARGENTINA – CERAMIC TILES", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2 and 6"], "articles": [], "subject": "Argentina's definitive anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 and Annex II (evidence – facts available): The Panel found that Art. 6.8, in conjunction with Annex II(6), requires an investigating authority to inform the party supplying information on the reasons why evidence or information is not accepted, to provide an opportunity to provide further explanation within a reasonable period, and to give, in any published determinations, the reasons for the rejection of evidence of information. The Panel then concluded that the Argentine investigating authority (DCD) acted inconsistently with these requirements under Art. 6.8 by failing to explain its evaluation of the information that led it to disregard in large part the information provided by exporters, resorting instead to the use of facts available. The Panel also rejected Argentina's various justifications for relying on facts available. • ADA Art. 6.10 (evidence – individual dumping margins): The Panel found that the DCD acted inconsistently with Art. 6.10 by imposing the same ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS192", "title": "US – COTTON YARN", "complainant": "Pakistan", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6"], "articles": [], "subject": "Transitional safeguard remedy imposed by the United States under the ATC on certain imports.", "sector": "Safeguards", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ATC Art. 6.2 (transitional safeguard measure – scope of domestic industry): The Appellate Body upheld the Panel's ultimate conclusion that the United States acted inconsistently with Art. 6.2 by excluding from the scope of the domestic industry captive production of yarn (i.e. yarn produced by and processed and consumed within integrated producers for their own use and processing), which was found to be “directly competitive” with yarn offered for sale on the merchant (open) market. In this regard, the Appellate Body considered the term “directly competitive” to suggest a focus on the competitive relationship of products, including not only actual but also “potential competition”. • ATC Art. 6.4 (transitional safeguard measures – attribution of serious damage): The Appellate Body found that (i) Art. 6.4 requires a “comparative analysis” when there is more than one Member from whom imports have shown a sharp and substantial increase and (ii) under such a comparative analysis, “the ful", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS194", "title": "US – EXPORT RESTRAINTS", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 1.1"], "articles": [], "subject": "Treatment of “export restraints” 2 under US countervailing duty (CVD) law (statute), in light of the relevant Statement of Administrative Action (SAA) and Preamble to CVD Regulations, and relevant Uni", "sector": "Subsidies & Anti-Subsidy", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (a): (1): (iv) (definition of a subsidy – financial contribution): The Panel first concluded that an “export restraint” cannot constitute government-entrusted or government-directed provision of goods in the sense of subpara. (iv) of Art. 1.1(a)(1), and thus does not constitute a “financial contribution” within the meaning of Art. 1.1. According to the Panel, the “entrusts or directs” standard of subpara. (iv) requires an “explicit and affirmative action of delegation or command”, rather definition of a subsidy – than mere government intervention in the market by itself which leads to a particular result or effect. • Nature of the US law at issue (mandatory vs discretionary): To answer the ultimate question of whether the United States was in violation of the ASCM, the Panel examined whether the US law at issue “required” the USDOC (i.e. executive branch of the government) to treat export restraints as “financial contributions” in CVD investigations. Having found that t", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS202", "title": "US – LINE PIPE", "complainant": "Korea, 5 and 9", "respondent": "United States", "third_parties": [], "agreements": [], "articles": [], "subject": "US safeguard measure on certain imports.", "sector": "Safeguards", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• SA Arts. 3.1 and 4.2(c) (safeguard investigation – injury determination): The Appellate Body reversed the Panel's finding that the United States violated Arts. 3.1 and 4.2(c) by failing to publish in its investigation report a discrete finding or reasoned conclusion that the increased imports caused either “serious injury” or “threat of serious injury”, on the ground that the phrase “cause or threaten to cause” should be read to mean that an investigating authority has to conclude either one or both in combination as the US authority had done in the case at hand. • SA Arts. 2 and 4 (parallelism): The Appellate Body reversed the Panel's finding that Korea did not make a prima facie case of violation of the “parallelism” requirement under Arts. 2 and 4, and concluded that the United States violated the Articles since it had excluded Canada and Mexico from the application of the measure without providing adequate reasoning, while including them in the investigation. • SA Art. 4.2(b) (in", "keywords": ["safeguards"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS204", "title": "MEXICO – TELECOMS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATS Art I:2(a)", "GATS Reference Paper under", "GATS Annex on Telecommunications"], "articles": [], "subject": "Mexico's domestic laws and regulations that govern the supply of telecommunication services and federal competition laws.", "sector": "Services", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2004", "summary_ar": "", "summary_en": "• GATS Art. I:2(a) (cross border supply): The Panel found that the services at issue whereby US suppliers link their networks at the border with those of Mexican suppliers for termination within Mexico are services supplied cross-border within the meaning of Art. I:2(a), as the provision is silent as regards the place where the supplier operates, or is present, and thus is not directly relevant to the definition of “cross-border supply”. • Mexico's Reference Paper3 , Sections 2.1 and 2.2: The Panel found that (i) Mexico's commitments under Section 2 of Mexico's Reference Paper applied to the interconnection of cross-border US companies seeking to supply the services at issue into Mexico ; and (ii) Mexico was in violation of its commitments under the provision because the interconnection rates charged by Mexico's major suppliers to US suppliers were not “cost-oriented” as they were in excess of the cost rate for providing the interconnection to the US suppliers. • Mexico's Reference Pap", "keywords": ["services", "GATS", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS206", "title": "US – STEEL PLATE", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 6.8, 15 and 18.4"], "articles": [], "subject": "US imposition of anti-dumping duties on certain imports manufactured by Steel Authority of India, Ltd. (SAIL).", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 18.4 (conformity with the ADA): The Panel held that the US authority's practice in the application of “facts available” was not a measure that could be the subject of a claim. First, because such practice could be changed by the authority as long as it provided a reason for the change. Moreover, according to past WTO jurisprudence, a law can only be found inconsistent with WTO obligations if it mandates a violation. Second, the “practice” challenged by India was not within the scope of Art. 18.4, which only refers to “laws, regulations and administrative procedures”. • ADA Art. 6.8 and Annex II(3) (evidence – facts available): (as applied claim) The Panel found that the US authority acted inconsistently with the ADA in finding that SAIL had failed to provide necessary information in response to questionnaires during the course of the investigation and in consequently basing their determination entirely on “facts available”, because the information provided by SAIL met all cr", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS211", "title": "EGYPT – STEEL REBAR", "complainant": "Turkey", "respondent": "Egypt", "third_parties": [], "agreements": ["ADA Arts. 2, 3 and 6"], "articles": [], "subject": "Egypt's definitive anti-dumping measures.", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 3.4 (injury determination – injury factors): The Panel interpreted evaluation under Art. 3.4 to mean a process of analysis and interpretation of the facts established, in relation to each listed factor. In the light of this interpretation, the Panel concluded that Egypt acted inconsistently with Art. 3.4 in failing to evaluate six of the factors (productivity, actual and potential negative effects on cash flow, employment, wages and ability to raise capital or investments) as claimed by Turkey but was not in violation with regard to two of the factors (capacity utilization, return on investment). • ADA Art. 6.8 and Annex II(6) (evidence – facts available): The Panel found that with respect to the investigation of two exporters, Egypt was in violation of Art. 6.8 and Annex II(6), as the investigating authorities, having identified and received the requested information from those companies, nevertheless concluded that the companies had failed to provide the “necessary informa", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS212", "title": "US – COUNTERVAILING MEASURES ON CERTAIN EC PRODUCTS", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1, 14 and 21"], "articles": [], "subject": "US countervailing duty law governing the treatment of subsidies provided to state-owned companies later privatized, including certain subsidy calculation methodologies developed by the United States D", "sector": "Subsidies & Anti-Subsidy", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• ASCM Arts. 1 (definition of a subsidy) and 14 (benefit – calculation of amount of subsidy): The Appellate Body reversed the Panel in its findings and stated instead that privatizations at arm's length and at fair market value gave rise to a rebuttable presumption that a benefit ceased to exist after such privatization. It shifts the burden on the investigation authority to establish that the benefits from the previous financial contribution does indeed continue beyond such privatization. • ASCM Art. 19.1 (original investigation), Art. 21.2 (administrative review) and Art. 21.3 (sunset review): Based on its analysis above on Arts. 1 and 14, the Appellate Body upheld the Panel's finding that the “same person” methodology was as such inconsistent with Arts. 19.1, 21.2 and 21.3. Based on this methodology and without further analysis, the USDOC had concluded that a privatized enterprise continued to receive the benefits of a previous financial contribution, irrespective of the price paid ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS213", "title": "US – CARBON STEEL", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 21.3"], "articles": [], "subject": "US laws, regulations, administrative procedures and policy bulletin governing “sunset” reviews of countervailing duties (CVDs), and their application in a sunset review of a CVD order on imports from ", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 21.3 (sunset review – de minimis standard): The Appellate Body reversed the Panel's finding that the US law was in violation of Art 21.3, on the grounds that Art. 21.3 does not require the application of a 1 per cent de minimis standard in sunset reviews. The Appellate Body disagreed with the Panel's reasoning that the de minimis requirement of Art. 11.9 of the ASCM (which applies to original investigations) is implied in Art. 21.3, on the grounds that Art. 21.3 does not have an express reference to the de minimis standard nor is there a textual link (cross-reference) between the two Articles. • ASCM Art. 21.3 (sunset review – initiation by investigating authority): The Appellate Body upheld the Panel's findings that the automatic self-initiation of sunset reviews by investigating authorities under US law and accompanying regulations are consistent with the ASCM. The Appellate Body stated that its review of the context of Art. 21.3 revealed no indication that the ability of", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS219", "title": "EC – TUBE OR PIPE FITTINGS", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["ADA Arts. 1, 2 and 3", "GATT Art. VI:2"], "articles": [], "subject": "EC Regulation imposing anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. VI:2 (imposition and collection of anti-dumping duties) and ADA Art. 1 (principles): The Appellate Body agreed with the Panel that there was nothing in the ADA that requires investigating authorities to reassess a determination of dumping on the basis of a devaluation occurring during the period of investigation (POI), and thus upheld the Panel's rejection of Brazil's claims. • ADA Art. 2.2.2, chapeau (dumping determination – normal value): The Panel rejected Brazil's claim that the EC authorities should have excluded low volume sales figures from their calculation of “normal value” on the ground that the chapeau only allows investigating authorities to exclude data from production and sales that were not made in the ordinary course of trade. The Appellate Body upheld the Panel's findings. • ADA Arts. 3.2 (injury determination – volume of imports) and 3.3 (injury determination – cumulative assessment of the effects of imports): The Appellate Body upheld the Panel's findings", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS231", "title": "EC – SARDINES", "complainant": "Peru", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Annex 1.1 and Art. 2.4"], "articles": [], "subject": "EC Regulation establishing common marketing standards for preserved sardines, including a specification that only products prepared from Sardina pichardus could be marketed/labelled as preserved sardi", "sector": "Standards & TBT", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "• TBT Agreement Annex 1.1 (technical regulation): The Appellate Body upheld the Panel's finding that the EC Regulation was a “technical regulation” within the meaning of Annex 1.1 as it fulfilled the three criteria laid down in the Appellate Body report in EC – Asbestos: (i) the document applied to an identifiable product or group of products; (ii) it lays down one or more product characteristics; and (iii) compliance with the product characteristics was mandatory. • TBT Agreement Art. 2.4 (international standard): The Appellate Body upheld the Panel's finding that the definition of “standard” does not require that a standard adopted by a “recognized body” be approved by consensus. Therefore, the standard in question, Codex Stan 94, fell within the scope of Art. 2.4 as well. • TBT Agreement Art. 2.4 (international standard – burden of proof): The Appellate Body reversed the Panel's finding that the European Communities had the burden of proving that the relevant international standard ", "keywords": ["standards & tbt", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS236", "title": "US – SOFTWOOD LUMBER III", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 14, 17 and 20"], "articles": [], "subject": "Preliminary countervailing duty determination and preliminary critical circumstances determination made by the US authorities in respect of lumber imports and US laws on expedited reviews and “adminis", "sector": "Subsidies & Anti-Subsidy", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a): (1): (iii) (definition of a subsidy – financial contribution): The Panel concluded that the US authorities' determination that the Canadian provincial stumpage programme constituted a “financial contribution” by the government within the terms of Art. 1.1(a)(iii) was not inconsistent with the ASCM. The Panel considered that the Canadian government act of allowing companies to cut the trees amounted to the “supply” of standing timber, which is a good within the meaning of Art. 1.1(a)(1)(iii). • ASCM Art. 14 and 14(d) (benefit – calculation of amount of subsidy): The Panel concluded that the US authorities acted inconsistently with Art. 14 and 14(d) by using the US stumpage prices instead of the prevailing market conditions for the product at issue in Canada, the country of provision or purchase, as required by Art. 14(d), in determining whether a “benefit” accrued from the Canadian government to the recipient. • ASCM Art. 1.1(b) (definition of a subsidy – benefit): T", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS238", "title": "ARGENTINA – PRESERVED PEACHES", "complainant": "Chile, 4.1 and 4.2", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Art. XIX:1(a)"], "articles": [], "subject": "Argentina's safeguard measures imposed, in the form of specific duties, on preserved peaches from all countries other than MERCOSUR States and South Africa.", "sector": "Safeguards", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): The Panel noted the two distinct requirements under Art. XIX:1(a) to be fulfilled before the imposition of safeguard measures: (i) demonstration of increased imports and (ii) demonstration of unforeseen developments. The Panel concluded that on the facts of the case it was not evident that the Argentine authorities had discussed or offered any explanation on why the developments were “unforeseen” at the time of the negotiation of the obligations, and, therefore, that they had not fulfilled the criteria of Art. XIX:1(a). • SA Arts. 2.1 and 4.2(a) and GATT Art. XIX:1(a) (conditions for safeguard measures – increased imports): The Panel noted that the increase in imports must be “qualitative” as well as “quantitative”, and concluded that the Argentine authorities had failed to demonstrate that: (i) they had considered trends in imports in absolute terms, which significantly showed a decline over the period of analysis; and (ii) the increase ", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS241", "title": "ARGENTINA – POULTRY ANTI-DUMPING DUTIES", "complainant": "Brazil", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 6"], "articles": [], "subject": "Definitive anti-dumping measures, in the form of specific anti-dumping duties, imposed by Argentina on imports from Brazil for a period of three years.", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Art. 5.3 (initiation of investigation – application): The Panel found that, by basing the determination of initiation of an investigation on “some” instances of dumping, Argentina violated Art. 5.3 as a dumping determination should be made in respect of the product as a whole for “all” comparable transactions, not for individual transactions. • ADA Art. 5.8 (initiation of investigation – insufficient evidence): The Panel found that Argentina violated Art. 5.8 as it failed to reject an application for investigation which was based on insufficient evidence following the issuance of a negative injury determination from the relevant investigation authority. • ADA Art. 6.8 (evidence – facts available): The Panel found that Argentina was not in violation of Art. 6.8 when it disregarded information submitted by a company that had not fulfilled procedural provisions of the domestic law. As information submitted by such companies was not considered “appropriately submitted” within the mea", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS243", "title": "US – TEXTILES RULES OF ORIGIN", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ROA Art. 2"], "articles": [], "subject": "Rules of origin applied by the United States to textiles and apparel products and used in administering the textile quota regime maintained by the United States under the Agreement on Textiles and Clo", "sector": "Textiles", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• ROA Art. 2(b) (trade objectives): The Panel rejected India's claim and concluded that although the objectives of protecting the domestic industry against import competition and of favouring imports from one Member over imports from another may in principle be considered to constitute “trade objectives” for which rules of origin may not be used, India had failed to establish that US rules of origin were being administered to pursue trade objectives in violation of Art. 2(b). • ROA Art. 2(c), first sentence (restrictive, distorting or disruptive effects): The Panel rejected India's claim on the grounds that for there to be a violation of Art. 2(c), it must be proved that there is a causal link between the challenged rules of origin itself and the prohibited effects. The Panel further recognized that it would not always and necessarily be sufficient for a complaining party to show that the challenged rules of origin adversely affect one Member's trading as it may favourably affect the t", "keywords": ["textiles", "ROA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS244", "title": "US – CORROSION RESISTANT STEEL SUNSET REVIEW", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 11.3"], "articles": [], "subject": "(i) US statute for sunset review of anti-dumping duties, in conjunction with the Statement of Administrative Action (SAA), certain provisions of the US regulations related to sunset reviews and the Su", "sector": "Metals & Mining", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review • ADA Art. 11.3 (continuation of dumping and injury): The Appellate Body made some general observations with regard to such a determination: (i) the second condition of Art. 11.3 involved a prospective determination on the part of the investigating authorities, requiring a forward-looking analysis of what would be likely to occur if the duty were terminated; (ii) as to the standard of “likely”, a positive determination may be made only if the evidence demonstrated that dumping would be “probable” (not possible or plausible) if the duty were terminated; and (iii) Art. 11.3 does not prescribe any particular methodology to be used by investigating authorities in making a likelihood determination. • ADA Arts. 11.3 and 2.4 (fair comparison): The Appellate Body reversed the Panel's finding and concluded that the United States violated Art. 11.3 by relying on dumping margins calculated in previous reviews using the “zeroing” methodology. While there is no obligation under Art. 1", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS245", "title": "JAPAN – APPLES", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7 and 5.1", "DSU Art. 11"], "articles": [], "subject": "Certain Japanese measures restricting imports of apples on the basis of concerns about the risk of transmission of fire blight bacterium.", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that the measure was maintained “without sufficient scientific evidence” inconsistently with Art. 2.2, as there was a clear disproportion (and thus no rational or objective relationship) between Japan's measure and the “negligible risk” identified on the basis of the scientific evidence. • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the measure was not a provisional measure justified within the meaning of Art. 5.7, as the measure was not imposed in respect of a situation “where relevant scientific evidence is insufficient”. Having noted that the pertinent question under Art. 5.7 is whether the body of available scientific evidence does not allow, in quantitative or qualitative terms, the performance of an adequate assessment of risks as required under Art. 5.1 and as defined in Annex A of the SPS Agreement, the Appellate Body found that in light of t", "keywords": ["agriculture & food", "SPS", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS264", "title": "US – SOFTWOOD LUMBER V", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 4, 5, 6, 9 and 18"], "articles": [], "subject": "US final anti-dumping duties.", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Dumping determination • ADA Art. 2.4 and 2.4.2 (zeroing): The Appellate Body upheld the Panel's (majority) finding that the US acted inconsistently with the first sentence of Art. 2.4.2 in determining dumping margins on the basis of a methodology incorporating zeroing in the aggregation of results of comparisons of weighted average normal value with a weighted average of prices of all comparable export transactions. The Appellate Body ruled in this case only on the first methodology provided for in Art. 2.4.2, first sentence, that is weighted average normal value compared with a weighted average of export prices • ADA Art. 2.2.1.1, 2.2.2 and 2.4 (allocation of financial expenses): The Appellate Body reversed the Panel's legal interpretation under Art. 2.2.1.1 of the phrase “consider all available evidence on the proper allocation of costs” that an investigating authority is never required to “compare various cost allocation methodologies to assess their advantages and disadvantages” an", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS265", "title": "EC – EXPORT SUBSIDIES ON SUGAR", "complainant": "Australia, Thailand, Brazil, 8 and 9.1", "respondent": "European Communities", "third_parties": [], "agreements": [], "articles": [], "subject": "EC measures relating to subsidization of the sugar industry, namely, a Common Organization for Sugar (CMO) (set out in Council Regulation (EC) No. 1260/2001): two categories of production quotas – “A ", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• EC export subsidy commitment levels for sugar: The Appellate Body upheld the Panel's finding that footnote 1 in the EC Schedule relating to preferential imports from certain ACP countries and India did not have the legal effect of enlarging or otherwise modifying the European Communities' quantity commitment level contained in Section II, Part IV of its Schedule. • AA Arts. 9.1(c), 3.3 and 8 (export subsidies – exports of C sugar): The Appellate Body upheld the Panel's finding that the European Communities violated Arts. 3.3 and 8 by exporting C sugar because export subsidies in the form of payments on the export financed by virtue of government action within the meaning of Art. 9.1(c) were provided in excess of the European Communities' commitment level. In this regard, the European Communities provided two types of “payments” within the meaning of Art. 9.1(c) for C sugar producers, i.e. (i) sales of C beet below the total costs of production to C sugar producers; and (ii) transfers", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS267", "title": "US – UPLAND COTTON (ARTICLE 21.5 – BRAZIL)", "complainant": "Brazil", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts.3, 5(c), 6.3(c), and item", "DSU Arts. 11 and 21.5"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2008, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2008", "summary_ar": "", "summary_en": "• AA Arts. 10.1 and 8, and ASCM Arts 3.1(a), 3.2 and the Illustrative List of Export Subsidies, item (j): The Appellate Body upheld the Panel's finding that export credit guarantees provided under the revised GSM 102 programme were “export subsidies” because the premiums charged were inadequate to cover the long-term operating costs and losses of the programme, within the meaning of item (j) of the Illustrative List. The Appellate Body upheld the Panel's finding under item (j) despite having found that the Panel's analysis of certain quantitative evidence concerning the financial performance of the revised GSM 102 programme did not meet the requirements of DSU Art. 11. Upon finding that the Panel acted inconsistently with DSU Art. 11, the Appellate Body completed the analysis and found that the Panel's finding on the structure, design, and operation of the revised GSM 102 programme, in the light of the quantitative evidence, provided a sufficient evidentiary basis for the conclusion th", "keywords": ["subsidies & anti-subsidy", "ASCM", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS268", "title": "US – OIL COUNTRY TUBULAR GOODS SUNSET REVIEWS", "complainant": "Argentina, Annex II", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 3, 6,11,12, 18 and"], "articles": [], "subject": "US anti-dumping duties as well as laws, regulations and practice governing sunset reviews under the Sunset Policy Bulletin (SPB).", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review (ADA Art. 11.3): as such violations • SPB (DSU Art. 11): The Appellate Body upheld the Panel's finding that the SPB was a “measure” subject to WTO dispute settlement; however, due to what it considered to be an insufficient analysis, it found that the Panel had failed to make an objective assessment of the matter within the meaning of DSU Art. 11 and reversed the Panel's finding that Section II.A.3 of the SPB was inconsistent, as such, with Art. 11.3. It did not complete the analysis on this issue. • “Affirmative and deemed waiver provisions”:3 The Appellate Body upheld the Panel's findings that the waiver provisions relating to waiver of participation in sunset review proceedings were, as such, inconsistent with the requirements relating to the likelihood of dumping determination under Art. 11.3 because they required assumptions about a company's likelihood of dumping. Also, having concluded that the respondents' incomplete substantive submissions should still be taken i", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS269", "title": "EC – CHICKEN CUTS", "complainant": "Thailand, Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II:1"], "articles": [], "subject": "EC measures pertaining to the tariff reclassification from heading 02.10 (relating to, inter alia, salted chicken) to heading 02.07 (relating to, inter alia, frozen chicken) of certain frozen boneless", "sector": "Other", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body upheld the Panel's ultimate finding that the EC measures (relating to tariff classification) imposed duties on the products at issue in excess of the relevant heading of the EC tariff commitment because under the EC Schedule, tariffs on frozen meat (02.07) are higher than on salted meat (02.10) and, thus, violated Arts. II:1(a) and (b). Interpretation3 of the term at issue “salted” in EC Schedule • Ordinary meaning (VCLT Art. 31(1)): The Appellate Body upheld the Panel's finding that “in essence, the ordinary meaning of the term 'salted' ... indicates that the character of a product has been altered through the addition of salt” and that “there is nothing in the range of meanings comprising the ordinary meaning of the term 'salted' that indicates that chicken to which salt has been added is not covered by the concession contained in heading 02.10 of the EC Schedule”. • Context (VCLT Art. 31(2)): Having considered relevant ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS273", "title": "KOREA – COMMERCIAL VESSELS", "complainant": "European Communities, 6.3(a)", "respondent": "Korea", "third_parties": [], "agreements": ["ASCM Arts. 3.1(a),3.2, 4.7, 5(c) and"], "articles": [], "subject": "Korea's various measures relating to alleged subsidies to its shipbuilding industry.2", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "ASCM Art. 3.1(a) and 3.2 (export subsidies) • Measures as such: Having found that the KEXIM legal regime (KLR), APRG and PSL programmes did not “mandate” the conferral of a “benefit,” the Panel rejected EC claims that these measures as such were inconsistent with Art. 3.1(a) and 3.2. • Measures as applied: The Panel found that certain “KEXIM guarantees” under the APRG programme were prohibited export subsidies (specific subsidies contingent upon export performance) under Art. 3.1(a) and 3.2 and rejected Korea's argument that item (j) (i.e. export credit guarantee) of the Illustrated List could work as an affirmative defence, on the ground that item (j) does not fall within the scope of footnote 54 of ASCM. The Panel also found that certain “KEXIM loans” under the PSL programme were prohibited export subsidies and rejected Korea's defence under item (k) (export credit grants) since the PSLs (as credits to shipbuilders rather than foreign buyers) were not export credits. ASCM Part III (a", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS276", "title": "CANADA – WHEAT EXPORTS AND GRAIN IMPORTS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. XVII:1 and III:4"], "articles": [], "subject": "Canadian Wheat Board (CWB) Export Regime2 and requirements related to the import of grain into Canada.", "sector": "Agriculture & Food", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2004", "summary_ar": "", "summary_en": "GATT Art. XVII:1 (State Trading Enterprise (STE)) • Relationship between paras. (a) and (b) of Art. XVII:1: The Appellate Body reasoned that subpara. (a) is the general and principal provision, and subpara. (b) explains it by identifying the types of differential treatment in commercial transactions that are most likely to occur in practice. Therefore, most, if not all, claims raised under Art. XVII:1 will require a sequential analysis of both subparas. (a) and (b). At the same time, because both subparas. (a) and (b) define the scope of that non-discrimination obligation, panels would not always be in a position to make any finding of violation of Art. XVII:1 until they have properly interpreted and applied both provisions. The Appellate Body, however, rejected Canada's contention that the Panel's approach constituted legal error. Although the Panel refrained from explicitly defining the relationship between the first two subparas. of Art. XVII:1 and proceeded on the basis of an assum", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS282", "title": "US – ANTI-DUMPING MEASURES ON OIL COUNTRY TUBULAR GOODS", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 3 and 11"], "articles": [], "subject": "Determinations by the United States Department of Commerce (USDOC) and the International Trade Commission (ITC) in the sunset review of the anti-dumping duties on Oil Country Tubular Goods (OCTG) impo", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Art 11.3 (review of anti-dumping duties): The Appellate Body reversed the Panel's finding that the Sunset Policy Bulletin (SPB) as such was inconsistent with ADA Art. 11.3 due to the Panel's failure to make “an objective assessment of the matter and the facts of the case” as required by DSU Art. 11. The Panel initially found that the SPB established an “irrebuttable presumption” of likelihood of dumping inconsistently with ADA Art. 11.3, as the USDOC treated the standard set out in SPB as conclusive or determinative as to the “likelihood” of continuation or recurrence of dumping in “sunset reviews”. • ADA Art. 11.3 (review of anti-dumping duties – likelihood of dumping): The Panel concluded that the USDOC's determination of likelihood of continuation or recurrence of dumping in the sunset review at issue was inconsistent with Art. 11.3 because it had failed to consider relevant evidence submitted by Mexican exporters and almost exclusively relied on the basis of a decline in impo", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS285", "title": "US – GAMBLING", "complainant": "Antigua and Barbuda", "respondent": "United States", "third_parties": [], "agreements": ["GATS Arts. XIV(a) and XIV(c) and XVI"], "articles": [], "subject": "Various US measures relating to gambling and betting services, including federal laws such as the “Wire Act”, the “Travel Act” and the “Illegal Gambling Business Act” (IGBA).", "sector": "Services", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• Scope of GATS commitments: The Appellate Body upheld, based on modified reasoning, the Panel's finding that the US GATS Schedule included specific commitments on gambling and betting services. Resorting to “document W/120” and the “1993 Scheduling Guidelines”3 as “supplementary means of interpretation” under Art. 32 of the VCLT, rather than context (Art. 31), the Appellate Body concluded that the entry, “other recreational services (except sporting)”, in the US Schedule must be interpreted as including “gambling and betting services” within its scope. • GATS Art. XVI:1 and 2 (market access commitment): The Appellate Body upheld the Panel's finding that the United States acted inconsistently with Art. XVI:1 and 2, as the US federal laws at issue, by prohibiting the cross-border supply of gambling and betting services where specific commitments had been undertaken, amounted to a “zero quota” that fell within the scope of, and was prohibited by, Art. XVI:2(a) and (c). However, it revers", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS294", "title": "US – ZEROING (EC)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 9.3, 2.4 and 2.4.2", "GATT Art. VI:2"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in determining dumping margins in anti-dumping proceedings as well as the zeroing methodology as such. 2. SUMMARY OF KEY PANEL/AB FINDINGS As appl", "sector": "Anti-Dumping", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2006", "summary_ar": "", "summary_en": "As applied claims • ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that the zeroing methodology, as applied by the United States in the administrative reviews at issue, was inconsistent with ADA Art. 9.3 and GATT Art. VI:2, as it resulted in amounts of anti-dumping duties that exceeded the foreign producers’ or exporters’ margins of dumping. Under ADA Art. 9.3 and GATT Art. VI:2, investigating authorities are required to ensure that the total amount of anti-dumping duties collected on the entries of a product from a given exporter shall not exceed the margin of dumping established for that exporter. • ADA Art. 2.4, third to fifth sentences (dumping determination – due allowance or adjustment): The Appellate Body agreed with the Panel that, conceptually, zeroing is not “an allowance or adjustment” falling within the scope of Art. 2.4, third to fifth sentences, which covers allowances or adjustments that a", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS295", "title": "MEXICO – ANTI-DUMPING MEASURES ON RICE", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["ADA Arts. 3, 5.8, 6, 9, 11 12 and 17"], "articles": [], "subject": "Mexico's definitive anti-dumping duties; several provisions of Mexico's Foreign Trade Act; and the Federal Code of Civil Procedure.", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 3.1, 3.2, 3.4 and 3.5 (injury determination – period for the injury investigation): The Appellate Body upheld the Panel's finding that Mexico violated Arts. 3.1, 3.2, 3.4 and 3.5, as it based its determination of injury on a period of investigation which ended more than 15 months before the initiation of the investigation, and thus it had failed to make an injury determination based on positive evidence, and involving an objective examination of the volume and price effects of the alleged dumped imports or the impact of the imports on domestic producers at the time measures were imposed under Art. 3. • ADA Art. 3.1 (injury determination – use of data from part of the investigation period): The Appellate Body upheld the Panel's finding that the investigating authority's injury analysis was inconsistent with Art. 3.1 because it examined only part of the data from the investigation period and the choice of the limited period of investigation reflected the highest import penetr", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS299", "title": "EC – COUNTERVAILING MEASURES ON DRAM CHIPS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 12, 14 and 15"], "articles": [], "subject": "EC definitive countervailing duties.", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1)(iv) (definition of a subsidy – financial contribution): The Panel held that the European Communities' “financial contribution” finding with respect to one of Korea's five alleged subsidy programmes3 was inconsistent with Art. 1.1(a) (1)(iv), as it considered that the evidence before the EC investigating authority (i.e. government official's presence at Hynix's Creditor Council meeting) was insufficient for it to reasonably conclude that the Korean government entrusted or directed the private banks to purchase Hynix convertible bonds. The Panel held that the European Communities' finding on the other four programmes was consistent with Art. 1.1(a). • ASCM Arts. 1.1(b) and 14 (definition of a subsidy – benefit): The Panel found that the European Communities failed to establish the “existence” of a “benefit” from the financial contribution provided under one of the programmes (i.e. Syndicated Loan) within the meaning of Art 1.1(b), as it had ignored the loans provide", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS301", "title": "EC – COMMERCIAL VESSELS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. III:4, I:1 and III:8(b)", "DSU Art. 23.1", "ASCM Art. 32"], "articles": [], "subject": "The European Communities' Temporary Defensive Mechanism for Shipbuilding (the “TDM Regulation”) of 2002, under which contract-related operating aid provided by EC member States for the building of cer", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Arts. III:4 (national treatment – domestic laws and regulations) and III:8(b) (national treatment – subsidies exception): The Panel concluded that the state aid subject to the TDM Regulation was covered by GATT Art. III:8(b) because it provided for “the payment of subsidies exclusively to domestic producers”, and therefore the TDM Regulation, the national TDM schemes (in this case, Denmark, France, Germany, the Netherlands and Spain) and the EC decisions authorizing the schemes were not inconsistent with GATT Art. III:4. • GATT Arts. I:1 (most-favoured-nation treatment) and III:8(b) (national treatment – subsidies exception): Based on its conclusion that the TDM Regulation was covered by GATT Art. III:8(b) and that, as a result, the subsidies under the TDM Regulation were not covered by the expression “matters referred to in paras. 2 and 4 of Article III” in Art. I:1, the Panel concluded that the TDM Regulation and the national TDM schemes were not inconsistent with GATT Art. I:", "keywords": ["subsidies & anti-subsidy", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS308", "title": "MEXICO – TAXES ON SOFT DRINKS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATT Arts. III and XX(d)"], "articles": [], "subject": "Mexico's tax measures under which soft drinks using non-cane sugar sweeteners were subject to 20 per cent taxes on (i) their transfer and importation; and (ii) specific services provided for the purpo", "sector": "Agriculture & Food", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2006", "summary_ar": "", "summary_en": "National treatment • GATT Arts. III:2 (national treatment – taxes and charges), first sentence (like products): As for soft drinks sweetened with HFCS, the Panel found that the tax measures were inconsistent with Art. III:2, first sentence, as these drinks were subject to internal taxes (20 per cent transfer and services taxes) in excess of taxes imposed on like domestic products – i.e. soft drinks sweetened with cane sugar (exemption from those taxes). • GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): As for non-cane sugar sweeteners such as HFCS, the Panel found that the tax measures were inconsistent with Art. III:2, second sentence as “the dissimilar taxation (i.e. 20 per cent transfer and services taxes)” imposed on “directly competitive or substitutable imports (HFCS) and domestic products (cane sugar)” was applied in a way that afforded protection to domestic production. • GATT Art. III:4 (national treat", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS312", "title": "KOREA – CERTAIN PAPER", "complainant": "Indonesia", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6, 9, 12 and Annex II"], "articles": [], "subject": "Anti-dumping duties imposed by Korea on certain imports.", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 2,2, 6.8 and Annex II(3) (dumping determination – facts availabe): The Panel found that the Korean investigating authority (i.e. KTC) did not act inconsistently with Art. 6.8 and Annex II(3) when it resorted to facts available for the calculation of normal value for two Indonesian exporters because the information requested (financial statements and accounting records) had not been submitted “within a reasonable period of time”. In addition, the data submitted to the KTC after the deadline were not verifiable within the meaning of Annex II(3) in light of the fact that the exporters refused to submit corroborating information during the verification. The Panel also found that the KTC complied with its obligation under Annex II(6) to inform the exporters of its decision to use facts available. The Panel also found that the KTC did not act inconsistently with Art. 2.2 in basing its normal value determination on constructed value under Art. 2.2, as the data (on domestic sales) ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS322", "title": "US – ZEROING (JAPAN)", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 9 and 11", "GATT Arts. VI", "DSU Art. 11"], "articles": [], "subject": "The United States' “zeroing” procedures in the context of original investigations, periodic reviews, new shipper and changed circumstances reviews, and sunset reviews; and the application of “zeroing”", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "As such claims • ADA Arts. 2.1, 2.4 and 2.4.2 and GATT Arts. VI:1 and VI:2 (zeroing in transaction-to-transaction comparisons in original investigations): The Appellate Body reversed the Panel's finding that the United States did not act inconsistently with Arts. 2.1, 2.4, and 2.4.2 by maintaining zeroing procedures in original investigations when calculating margins of dumping on the basis of transaction-to-transaction comparisons. The Appellate Body noted that because dumping and margins of dumping can only be found to exist in relation to the product under investigation, and not at the level of an individual transaction, all of the comparisons of normal value and export price must be considered. By disregarding certain comparison results, the United States acted inconsistently with Art. 2.4.2, with the “fair comparison” requirement of Art. 2.4, given that zeroing artificially inflates the magnitude of dumping. • ADA Arts. 2.1, 2.4, 9.1, 9.3 and 9.5 and GATT Arts VI:1 and VI:2 (zeroi", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS332", "title": "BRAZIL – RETREADED TYRES", "complainant": "European Communities, and (d), and XXIV", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I:1, III:4 , XI:1, XIII:1, XX(b)"], "articles": [], "subject": "(i) Brazil's import prohibition on retreaded tyres (Import Ban); (ii) fines on importing, marketing, transportation, storage, keeping or warehousing of retreaded tyres; (iii) Brazilian state law restr", "sector": "Other", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2007", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel concluded that Brazil's import prohibition on retreaded tyres and the fines imposed by Brazil on importation, marketing, transportation, storage, keeping or warehousing of retreaded tyres were inconsistent with Art. XI:1. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure maintained by the Brazilian State of Rio Grande do Sul in respect of retreaded tyres, Law 12.114, as amended by Law 12.381, was inconsistent with Art. III:4. • GATT Art. XX(b) (general exceptions – necessary to protect human life or health): The Appellate Body upheld the Panel's finding that the Import Ban was provisionally justified as “necessary” within the meaning of Art. XX(b). The Panel “weighed and balanced” the contribution of the Import Ban to its stated objective against its trade restrictiveness, taking into account the importance of the underlying interests or values. The Panel correctl", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS335", "title": "US – SHRIMP (ECUADOR)", "complainant": "Ecuador", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States' final anti-dumping measures including margins of dumping calculated using “zeroing” under the weighted-average-to weighted-average methodology.", "sector": "Agriculture & Food", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2007", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel found that the United States Department of Commerce “USDOC” acted inconsistently with the first sentence of Art. 2.4.2 by using “zeroing” in calculating margins of dumping under the weighted-average-to-weighted-average methodology in the context of an original investigation.", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS339", "title": "CHINA – AUTO PARTS", "complainant": "United States, Communities, Canada", "respondent": "China", "third_parties": [], "agreements": ["GATT Arts. II, III:2, III:4, XX(d)"], "articles": [], "subject": "Three legal instruments enacted by China2 which impose a 25 per cent “charge” 3 on imported auto parts “characterized as complete motor vehicles” based on specified criteria and prescribe administrati", "sector": "Automotive", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2009", "summary_ar": "", "summary_en": "• “Ordinary customs duty” vs “internal charge”: As a preliminary “threshold” issue, the Appellate Body upheld the Panel's characterization of the charge as an “internal charge” (Art. III:2), rather than as an “ordinary customs duty” (first sentence, Art. II:1(b)), because, after considering the characteristics of the measure, the Panel had properly ascribed legal significance to, inter alia, the fact, that the obligation to pay the charge accrues internally, after auto parts enter China. • GATT Arts. III:2 (national treatment – taxes and charges) and III:4 (national treatment – domestic laws and regulations): The Appellate Body upheld the Panel's findings that the measures violated: (i) Arts. III:2 because they imposed an internal charge on imported auto parts that was not imposed on like domestic auto parts; and (ii) Art. III:4 because they accorded imported parts less favourable treatment than like domestic auto parts by, inter alia, subjecting only imported parts to additional admin", "keywords": ["automotive", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS344", "title": "US – STAINLESS STEEL (MEXICO)", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 9.3", "GATT Art. VI:2", "DSU Art. 11"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in anti-dumping proceedings as well as the zeroing methodology as such.", "sector": "Metals & Mining", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2008", "summary_ar": "", "summary_en": "• ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that zeroing in administrative reviews is, as such, inconsistent with GATT Art. VI:2 and ADA Art. 9.3 because it results in the levying of anti-dumping duties that exceed the exporter's or foreign producer's margin of dumping – which operates as a ceiling for the amount of anti-dumping duties that can be levied in respect of the sales made by an exporter. The Appellate Body saw no basis in GATT Arts. VI:1 and VI:2 or in ADA Arts. 2 and 9.3 for disregarding the results of comparisons where the export price exceeds the normal value when calculating the margin of dumping for an exporter or foreign producer. Based on the same reasoning, the Appellate Body also found that the United States acted inconsistently with its obligations under GATT Art. VI:2 and ADA Art. 9.3 by using simple zeroing in five specific administrative reviews. • Status of Appellate Body re", "keywords": ["metals & mining", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS350", "title": "US – CONTINUED ZEROING", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Arts. 6.2 and 11", "ADA Arts. 2.4.2, 9.3, 11.3 and", "GATT Art. VI:2"], "articles": [], "subject": "The European Communities challenged as a measure the ongoing application by the United States of antidumping duties resulting from anti-dumping orders in 18 specific cases, as calculated with the use ", "sector": "Anti-Dumping", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2009", "summary_ar": "", "summary_en": "• ADA Art. 9.3, GATT Art. VI:2 and ADA Art. 11.3 (ongoing application of anti-dumping duties calculated with zeroing): The Appellate Body reversed the Panel's finding that the European Communities failed in its request for panel establishment to identify the measure in 18 anti-dumping cases. The Appellate Body found that the panel request identified the specific measures at issue as the continued application of anti-dumping duties calculated with the use of the zeroing methodology in each of the 18 cases listed in the annex to the panel request. The Appellate Body considered these measures to be neither rules nor norms of general application, nor specific instances of application of the zeroing methodology. Rather, they constituted ongoing conduct, which the European Communities was not precluded from challenging in WTO dispute settlement. With respect to four of the 18 cases, the Appellate Body completed the analysis and found that the continued application of anti-dumping duties was ", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS360", "title": "INDIA – ADDITIONAL IMPORT DUTIES", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. II:1(b) and II.2(a)"], "articles": [], "subject": "Two border charges, consisting of the “Additional Duty” imposed by India on imports of alcoholic beverages (beer, wine, and distilled spirits); and the “Extra-Additional Duty” imposed by India on impo", "sector": "Other", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2008", "summary_ar": "", "summary_en": "• GATT Arts. II:1(b) and II:2(a) (schedules of concessions): The Appellate Body reversed the Panel's finding that the United States had failed to establish that the Additional Duty and the Extra-Additional Duty were inconsistent with Arts. II:1(b) and II:2(a). The Appellate Body explained that it did not see a textual or other basis for the Panel's conclusion that “inherent discrimination” is a relevant or necessary feature of charges covered by Art. II:1(b). The Appellate Body further found that the Panel erred in its interpretation of the two elements of Art. II:2(a), that is “equivalence” and “consistency with Art. III:2”. In particular, the Appellate Body disagreed with the Panel's conclusion that the term “equivalent” does not require any quantitative comparison of the charge and internal tax. Instead, the Appellate Body considered that the term “equivalent” calls for a comparative assessment that is both qualitative and quantitative in nature. Moreover, the Appellate Body clarifi", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS375", "title": "EC – IT PRODUCTS", "complainant": "United States, Japan, Chinese Taipei, Taipei", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. II:1(a), II:1(b), X:1 and X:2"], "articles": [], "subject": "Various EC measures pertaining to the tariff classification, and consequent tariff treatment, of certain information technology products (IT products).", "sector": "Other", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2010", "summary_ar": "", "summary_en": "• The Ministerial Declaration on Trade in Information Technology Products (ITA): The European Communities had committed in its WTO Schedule to provide duty‑free treatment to certain IT products pursuant to the ITA. The products receiving duty-free treatment were indicated in the ITA in two ways: as HS1996 headings and in “narrative description” form. • GATT Arts. II:1(a) and II:1(b) (schedules of concessions – FPDs): The Panel found that the measures at issue were inconsistent with Arts. II:1(a) and II:1(b) because they required EC member States to classify some FPDs under dutiable headings although such products fell within the scope of the “narrative description” and/or within the scope of the CN code 8471 60 90 (which pertains to “input or output units” of “automatic data-processing machines” (ADP)), both of which were duty-free in the EC Schedule pursuant to the European Communities' implementation of the ITA.3 • GATT Arts. II:1(a) and II:1(b) (schedules of concessions – STBCs): Th", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS381", "title": "US – TUNA II (MEXICO)", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["TBT Annex 1.1, Arts. 2.1, 2.2 and 2.4", "DSU Art. 11", "GATT Arts. I:1 and III:4"], "articles": [], "subject": "(1) United States Code, Title 16, Section 1385 – “Dolphin Protection Consumer Information Act” (DPCIA); (2) Code of Federal Regulations, Title 50, Section 216.91 “Dolphin-safe labelling standards” and", "sector": "Standards & TBT", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (definition of technical regulation): The Appellate Body found that “the US measure establishes a single and legally mandated set of requirements for making any statement with respect to the broad subject of ‘dolphin-safety’ of tuna products in the United States”. Thus, it upheld the Panel’s ruling characterizing the measure at issue as a “technical regulation” within the meaning of TBT Annex 1. • TBT Art. 2.1 (national treatment – technical regulations): According to the Appellate Body, the measure at issue modified the competitive conditions in the US market to the detriment of Mexican tuna products and the United States did not demonstrate that this stemmed solely from “legitimate regulatory distinctions”. The Appellate Body, therefore found that the US “’dolphin-safe” labelling measure was inconsistent with Art. 2.1 and reversed the Panel’s contrary finding. • TBT Art. 2.2 (not more trade-restrictive than necessary): The Appellate Body disagreed with the Panel’s rul", "keywords": ["standards & tbt", "TBT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS382", "title": "US – ORANGE JUICE (BRAZIL)", "complainant": "Brazil", "respondent": "United States", "third_parties": [], "agreements": ["ADA. Art 2.4"], "articles": [], "subject": "United States Department of Commerce's (USDOC) (i) use of zeroing in two administrative reviews and (ii) “continued use” of zeroing in successive anti-dumping proceedings.", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (dumping determination – fair comparison): The Panel concluded that the use of zeroing to determine margins of dumping and importer-specific assessment rates was inconsistent with Art. 2.4 because it involves a comparison between export price and normal value that will invariably result in a higher margin of dumping than would otherwise be the case. In reaching this conclusion, the Panel clarified that, for systemic reasons, it followed the Appellate Body's previous findings on the United States' use of zeroing in anti-dumping proceedings. The Panel found that the United States had used “zeroing” to calculate the margins of dumping and the importer-specific rates of the two Brazilian respondents investigation in the First and Second Administrative Review and thus acted inconsistently with Art. 2.4. • ADA Art. 2.4 (dumping determination – continued use of zeroing): Brazil challenged the alleged continued use by the United States of zeroing in successive anti-dumping proce", "keywords": ["anti-dumping", "ADA."], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS384", "title": "US – COOL (ARTICLE 21.5 – CANADA AND MEXICO)", "complainant": "Canada, Mexico", "respondent": "United States", "third_parties": [], "agreements": ["TBT Arts. 2.1 and 2.2,", "GATT Arts. III:4, IX, XX, and XXIII:1(b)"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2015, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2015", "summary_ar": "", "summary_en": "• TBT Art. 2.1 (less favourable treatment and detrimental impact): The Appellate Body found that the Panel did not err in its consideration of (a) the increased recordkeeping burden entailed by the amended COOL measure; and (b) the potential for label inaccuracy under the amended COOL measure, as being within its analysis of whether the detrimental impact of that measure on imported livestock stemmed exclusively from legitimate regulatory distinctions. The Panel considered that the exemptions prescribed by the amended COOL measure supported a conclusion that the detrimental impact of that measure on imported livestock did not stem exclusively from legitimate regulatory distinctions. The Appellate Body upheld this finding. As regards, the cross appeals of Canada and Mexico, the Appellate Body found that the Panel did not err by considering the amended COOL measure's prohibition of a trace-back system as not relevant for the analysis of whether the detrimental impact of that measure on i", "keywords": ["anti-dumping", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS396", "title": "PHILIPPINES – DISTILLED SPIRITS", "complainant": "European Union, United States", "respondent": "Philippines", "third_parties": [], "agreements": ["GATT Art. III:2, first and"], "articles": [], "subject": "Philippines excise tax on distilled spirits, which imposed different tax rates depending on the raw material used to make the spirit.", "sector": "Other", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel’s finding that each type of imported distilled spirit at issue in this dispute – gin, brandy, vodka, whisky, and tequila – made from non-designated raw materials was “like” the same type of domestic distilled spirit made from designated raw materials, within the meaning of Art. III:2, first sentence. Accordingly, the Appellate Body upheld the Panel’s finding that, through its excise tax, the Philippines subjected specific types of imported distilled spirits to internal taxes in excess of those applied to like domestic spirits of the same type made from designated raw materials in violation of Art. III:2, first sentence. The Appellate Body, however, reversed the Panel’s additional finding that all distilled spirits at issue in the dispute, irrespective of their raw material base and their origin or type (brandy, whisky, rum, gin, vodka, tequila, and tequila-fla", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS399", "title": "US – TYRES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": [], "articles": [], "subject": "US transitional product-specific safeguard measure applied under para. 16 of China's Accession Protocol pursuant to Section 421 of the US Trade Act of 1974.", "sector": "Safeguards", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• China's Accession Protocol, para. 16.4 (imports “increasing rapidly”): The Appellate Body upheld the Panel's finding that the United States International Trade Commission (USITC) properly established that imports of subject tyres from China met the “increasingly rapidly” threshold provided in para. 16.4. The Appellate Body reasoned that such increases in imports must be occurring over a short and recent period of time, and must be of a sufficient magnitude in relative or absolute terms so as to be a significant cause of material injury to the domestic industry. • China's Accession Protocol, para. 16.4 (causation): The Appellate Body upheld the Panel's finding that the USITC properly demonstrated that subject imports were a “significant cause” of material injury. The Appellate Body found that the causal link expressed by the term “a significant cause” in para. 16.4 requires that rapidly increasing imports make an “important” or “notable” contribution in bringing about material injury ", "keywords": ["safeguards"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS400", "title": "EC – SEAL PRODUCTS", "complainant": "Canada, Norway", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Arts. 2.1, 2.2, 5.1.2, and 5.2.1", "GATT Arts. I:1, III:4, XI:I, XX(a) and"], "articles": [], "subject": "Regulations of the European Union (EU Seal Regime) generally prohibiting the importation and placing on the market of seal products, with certain exceptions, including for seal products derived from h", "sector": "Standards & TBT", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2014", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (technical regulation): The Appellate Body reversed the Panel’s intermediate finding that the EU Seal Regime lays down “product characteristics”, and consequently reversed the Panel’s finding that the EU Seal Regime was a “technical regulation” within the meaning of TBT Annex 1.1. The Appellate Body was unable to complete the legal analysis and thus did not rule on whether the EU Seal Regime lays down “related processes and production methods” within the meaning of TBT Annex 1.1. The Appellate Body therefore declared moot and of no legal effect the Panel’s conclusions under TBT Arts. 2.1, 2.2, 5.1.2, and 5.2.1. • GATT Art. I:1 (most-favoured-nation treatment): The Appellate Body upheld the Panel’s finding that the legal standard for the non-discrimination obligations under TBT Art. 2.1 does not apply equally to claims under GATT Art. I:1. The Appellate Body therefore upheld the Panel's finding that the EU Seal Regime was inconsistent with GATT Art. I:1 in respect of the", "keywords": ["standards & tbt", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS402", "title": "US – ZEROING (KOREA)", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "Certain United States final determinations and anti-dumping duty orders that included margins of dumping calculated using “zeroing” in the context of the “weighted-average to weighted-average” methodo", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – fair comparison): The Panel found that the United States acted inconsistently with the first sentence of Art. 2.4.2 by using the zeroing methodology in calculating certain margins of dumping in the context of the three original investigations at issue.", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS405", "title": "EU – FOOTWEAR (CHINA)", "complainant": "China", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.2, 6.5, 6.10, 9.2 and", "GATT Art. I"], "articles": [], "subject": "(1) Art. 9.5 of the European Union’s basic anti-dumping regulation (Basic AD Regulation), regulating dumped imports from non-market economies (NMEs); (2) the European Union “Definitive Regulation” imp", "sector": "Anti-Dumping", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2012", "summary_ar": "", "summary_en": "Claims related to the treatment of NMEs • ADA Arts. 6.10, 9.2, 18.4 and WTO Agreement Art. XVI:4 (individual treatment in imposing anti-dumping duties): ADA Arts. 6.10 and 9.2 support the same basic principle that individual exporters and producers in anti-dumping investigations should be treated individually in the determination and imposition of anti-dumping duties, except where it would be impracticable to do so. The Panel thus found that Art. 9.5 of the Basic AD Regulation was as such and as applied inconsistent with both of these provisions because, for NMEs, it imposed duties for producers/exporters on a country-wide basis and conditioned the calculation of individual duties on the satisfaction of individual treatment conditions. The Panel then concluded that Art. 9.5 of the Basic AD Regulation also violated WTO Agreement Art. XVI: 4 and ADA Art.18.4. • GATT Art. I:1 (most-favoured-nation treatment – treatment of NMEs): The Panel found Art. 9.5 of the Basic AD Regulation as such ", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS413", "title": "CHINA – ELECTRONIC PAYMENT SERVICES", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATS Arts. XVI and XVII"], "articles": [], "subject": "", "sector": "Services", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• Classification of the services at issue: The Panel found that electronic payment services for payment card transactions are classifiable under Subsector 7.B(d) of China’s Services Schedule, which reads “[a]ll payment and money transmission services, including credit, charge, and debit cards, travellers cheques and bankers drafts (including import and export settlement)”. It observed that the use of the term “all” manifests an intention to cover the entire spectrum of the “payment and money transmission services” encompassed under Subsector (d). • Scope of China’s GATS commitments: The Panel rejected the United States’ view that China’s Schedule includes a crossborder (mode 1) market access commitment to allow the supply of EPS into China by foreign EPS suppliers. The Panel found, however, that China’s Schedule includes a market access commitment that allows foreign EPS suppliers to supply their services through commercial presence (mode 3) in China, so long as a supplier meets certai", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS422", "title": "US – SHRIMP AND SAWBLADES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States anti-dumping measures covering two products from China.", "sector": "Agriculture & Food", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel upheld China’s claim that the use of zeroing in calculating the margins of dumping in the anti-dumping investigations at issue was inconsistent with Art. 2.4.2, and therefore concluded that the United States had acted inconsistently with its obligations under this provision. ADA Art. 2.4.2 (dumping determination – separate rate calculation): The Panel rejected China’s claim concerning the separate rate in the shrimp investigation. As the investigation concerned imports from a non-market economy, the United States Department of Commerce (USDOC) assigned a “separate rate” to exporters that were able to demonstrate the absence of government control, both de jure and de facto, over their export activities; other exporters were assigned the rate for the People’s Republic of China-entity. In calculating the separate rate, the USDOC had averaged the dumping margins of the investigated companies, which were calculated with zeroing. ", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS425", "title": "CHINA – X-RAY EQUIPMENT", "complainant": "European Union, 6.9 and 12.2.2", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4, 3.5, 6.5.1,"], "articles": [], "subject": "Anti-dumping duties imposed by China’s Ministry of Commerce (MOFCOM) by Notice No. 1 (2011), including its Annex, on x-ray equipment from the European Union.", "sector": "Anti-Dumping", "year": 2013, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2013", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 (injury determination) and 3.2 (injury determination – volume of imports): The Panel held that MOFCOM’s price undercutting and price suppression analyses were inconsistent with Arts. 3.1 and 3.2. The Panel found that the price effects analysis were not based on an objective examination of positive evidence, as MOFCOM had failed to ensure that the prices it was comparing as part of its price effects analysis were comparable. • ADA Arts. 3.1 (injury determination) and 3.4 ((injury determination – injury factors): The Panel found MOFCOM acted inconsistently with Arts. 3.1 and 3.4 because of its failure to consider all relevant economic factors, in particular, the “magnitude of the margin of dumping” when making a determination on the state of the domestic industry. Moreover, MOFCOM’s examination was found to lack objectivity, and not to be reasoned and adequate. The Panel rejected the European Union’s claim that MOFCOM did not rely upon positive evidence in making its dete", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS436", "title": "US – CARBON STEEL (INDIA)", "complainant": "India, 14(d)", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1(a)(1), 2.1, 12.7,"], "articles": [], "subject": "Imposition by the United States of countervailing duties on imports of certain hot-rolled carbon steel flat products from India.", "sector": "Metals & Mining", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2014", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Appellate Body reversed the Panel’s finding rejecting India’s claim that the United States Department of Commerce (USDOC) determination that the National Mineral Development Corporation (NMDC) was a public body was inconsistent with ASCM Art. 1.1(a)(1). The Appellate Body considered that the Panel had correctly articulated the appropriate standard but had erred in its substantive interpretation of ASCM Art. 1.1(a)(1) by construing the term “public body” to mean any entity that is “meaningfully controlled” by a government. Consequently, the Panel had erred in its application of ASCM Art. 1.1(a)(1) to the USDOC’s public body determination, in effect treating the Government of India’s (GOI) ability to control the NMDC as determinative for purposes of establishing whether the NMDC constituted a public body. The Panel had also failed properly to consider whether the USDOC had adequately explained and supported, in its written determin", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS437", "title": "US – COUNTERVAILING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI", "SCM Arts. 1.1, 1.1(a)(1), 1.1(b),", "DSU Arts. 6.2 and 11"], "articles": [], "subject": "Countervailing measures imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2015", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Panel found that the United States Department of Commerce (USDOC) acted inconsistently with Art. 1.1(a)(1), because it determined that certain Chinese state-owned enterprises were “public bodies” based solely on the grounds that they were majority owned, or otherwise controlled, by the Government of China. The Panel also found USDOC's “rebuttable presumption” to determine whether a state-owned enterprise is a “public body” to be inconsistent as such with Art. 1.1(a)(1). • ASCM Arts. 1.1(b) and 14(d) (benefit benchmark): The Panel found that the USDOC did not act inconsistently with Arts. 14(d) or 1.1(b) by rejecting in-country private prices in China as benchmarks in its benefit analysis. Noting that the selection of a benchmark under Art. 14(d) could not, at the outset, exclude consideration of in‑country prices from any particular source, including government‑related prices, the Appellate Body reversed the Panel's finding, and ", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS438", "title": "ARGENTINA – IMPORT MEASURES", "complainant": "European Union, United States, Japan", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. III:4 and XI:1"], "articles": [], "subject": "", "sector": "Other", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2015", "summary_ar": "", "summary_en": "• The Appellate Body upheld the Panel's finding that the Argentine authorities' imposition on economic operators of one or more five trade-related requirements (TRRs), as a condition to import or to obtain certain benefits, operated as a single measure attributable to Argentina (a TRRs measure). • DSU Art. 6.2 (requirements of panel request): The Appellate Body reversed the Panel's finding that 23 specific instances of application of the TRRs were not properly identified in the European Union's panel request as measures at issue and were not within the Panel's terms of reference. However, the Appellate Body found it unnecessary to complete the analysis with respect to those 23 specific instances of application of the TRRs, because the conditions on which the European Union based its appeal were not met. • GATT Art. XI (prohibition on quantitative restrictions): The Appellate Body upheld the Panel's finding that the TRRs measure was a restriction on the importation of goods, inconsisten", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS442", "title": "EU – FATTY ALCOHOLS (INDONESIA)", "complainant": "Indonesia", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 1, 2.3, 2.4, 2.6, 3.1, 3.2, 3.3, 3.4,", "GATT 1994 Arts. VI and X:3(a)", "DSU Arts. 3, 10.1, 11, 12.1, 12.7, 12.12, 17.4,"], "articles": [], "subject": "Anti-dumping duties imposed by the European Union on imports of fatty alcohols from Indonesia, and aspects of the underlying anti-dumping investigation.", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (fair comparison): The EU authorities made a downward adjustment to the export price of an Indonesian producer (PT Musim Mas) for payment made by PT Musim Mas to a related trading company based in Singapore (ICOF‑S). Indonesia claimed that PT Musim Mas and ICOF‑S formed a “single economic entity” and therefore, the payment (mark-up) was not a difference affecting price comparability within the meaning of Art. 2.4. The Appellate Body observed that the focus of Art. 2.4 is not merely on a comparison between the normal value and the export price, but predominantly on the means to ensure the fairness of that comparison. Pursuant to Art. 2.4, investigating authorities are required to make due allowance for differences affecting price comparability. There are no differences affecting price comparability that are precluded, as such, from being the object of an allowance. Instead, the need to make due allowances must be assessed in light of the specific circumstances of each cas", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS449", "title": "US – COUNTERVAILING AND ANTI-DUMPING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. X:1; X:2; X:3(b)", "SCM Arts. 10; 19.3; 32.1", "DSU Art. 6.2"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2014", "summary_ar": "", "summary_en": "• GATT Art. X:1 (trade regulations – prompt publication): In a finding not appealed, the Panel found that Section 1 of PL112‑99 was published promptly after it had been made effective because it was published on the same date that it was made effective, and thus the United States did not act inconsistently with Art. X:1 in respect of Section 1. • GATT Art. X:2 (trade regulations – no enforcement before publication): The Appellate Body reversed the Panel's finding that, although Section 1 of PL 112‑99 is a measure of general application that has been “enforced” prior to its official publication, it fell outside the scope of Art. X:2 because it neither effects an “advance” in a rate of duty on imports under an established or uniform practice, nor imposes a “new” or “more burdensome” requirement or restriction on imports. The Appellate Body considered that, to determine whether a measure of general application increases a rate of duty or imposes a new or more burdensome requirement, the b", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS461", "title": "COLOMBIA – TEXTILES", "complainant": "Panama", "respondent": "Colombia", "third_parties": [], "agreements": ["GATT Arts. II:1, II:1(b), VIII:1, X:3(a)"], "articles": [], "subject": "A compound tariff imposed by Colombia through Presidential Decree No. 074/2013, on imports of textiles, apparel and footwear, consisting of (i) a 10 per cent ad-valorem component; and (ii) a specific ", "sector": "Textiles", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body reversed the Panel's finding that it was unnecessary for the Panel to rule on whether Art. II:1 applies to “illicit trade”. The Appellate Body considered that the basis upon which the Panel had refrained from interpreting Art. II:1 was flawed. According to the Appellate Body, the Panel's statement implied that the measure at issue applied, or could apply, to some transactions considered by Colombia to be illicit trade, and thus the Panel was required to address the interpretative issue before it. The Appellate Body therefore found that the Panel acted inconsistently with the obligation in DSU Art. 11 to make an objective assessment of the matter, including an objective assessment of the applicability of the relevant covered agreements. In completing the legal analysis, the Appellate Body ruled that the scope of Art. II:1(a) and (b) did not exclude what Colombia classified as “illicit trade” from the requirements to respect", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS464", "title": "US – WASHING MACHINES", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2.4.2, 2.4, 9.3", "GATT Arts. VI:2, VI:3", "ASCM Arts. 2.2, 19.4"], "articles": [], "subject": "Definitive anti-dumping and countervailing duties applied by the US Department of Commerce (USDOC).", "sector": "Subsidies & Anti-Subsidy", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2, second sentence (pattern): The Appellate Body considered that a “pattern” comprises all export prices to a purchaser (or region or time period) which differ significantly from the export prices to other purchasers (or regions or time periods) because they are significantly lower than those other prices. The Appellate Body also found that the requirement to identify prices which differ significantly means that the authority is required to assess the price differences in a quantitative and qualitative manner. The Appellate Body thus reversed the Panel's findings to the extent it found that a pattern of export prices which differ significantly can be established “on the basis of purely quantitative criteria”. The Appellate Body held that an investigating authority must also explain why both the weighted average‑to‑weighted average (W-W) and the transaction‑to‑transaction methodologies (T-T) cannot take into account appropriately the identified differences in export price", "keywords": ["subsidies & anti-subsidy", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS473", "title": "EU – BIODIESEL (ARGENTINA)", "complainant": "Argentina, 2.4, 3.1, 3.4, 3.5, 9.3, 18.4, Establishment of Panel, 25 April 2014, Circulation of Panel Report, 29 March 2016, WTO Agreement Art. XVI:4, Circulation of AB Report, 6 October 2016, Adoption, 26 October 2016", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.1, 2.2, 2.2.1.1, 2.2.2 (iii),", "DSU Art. 11", "GATT Arts. VI:1, VI:1(b)(ii), VI:2"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Arts. 2.2.1.1 and 2.2 / GATT Art. VI:1(b)(ii) / DSU Art. 11 (as such claims): The Appellate Body upheld the Panel’s finding that Argentina had not established that the second subparagraph of Art. 2(5) of the Basic Regulation was inconsistent as such with Arts. 2.2.1.1, 2.2 and VI:1(b)(ii). • ADA Art. 2.2.1.1 (dumping determination – cost of production on the basis of records kept): The Appellate Body considered that the second condition in the first sentence of Art. 2.2.1.1 concerns whether the records kept by the investigated exporter/producer suitably and sufficiently correspond to or reproduce those costs incurred by the exporter/producer that have a genuine relationship with the production and sale of the product under consideration. Consequently, it upheld the Panel’s finding that the European Union acted inconsistently with this provision by failing to calculate the cost of production of the product under investigation on the basis of the records kept by the producers. • AD", "keywords": ["anti-dumping", "ADA", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS475", "title": "RUSSIA – PIGS (EU)", "complainant": "European Union, 5.2, 5.3, 5.6, 5.7, 6.1, 6.2, 6.3 and 8", "respondent": "Russia", "third_parties": [], "agreements": ["SPS Arts. 1, 2.2, 2.3, 3.1, 3.2, 5.1,"], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2017", "summary_ar": "", "summary_en": "• SPS Art. 3 (harmonization): The Panel found that the EU member State bans violated Art. 3.2 because they did not conform to the relevant OIE international standards. It found that the EU-wide ban and EU member State bans, except that in respect of Latvia, were inconsistent with Art. 3.1 because they were not based on the same standards. • SPS Arts. 5.1, 5.2, 5.3 and 2.2 (risk assessment): The Panel found that (i) the measures were not provisional measures under Art. 5.7, (ii) they violated Arts. 5.1 and 5.2 because they were not based on a risk assessment within the meaning of the Agreement, and (iii) without such a risk assessment, Russia could not have taken into account “relevant economic factors” as required by Art. 5.3. It found that Russia failed to rebut the presumption of inconsistency with Art. 2.2 raised by the violation of Arts. 5.1, 5.2 and 5.3. • SPS Art. 6 (adaptation to regional conditions): The Appellate Body upheld the Panel’s conclusion that the ban on imports from ", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS479", "title": "RUSSIA – COMMERCIAL VEHICLES", "complainant": "European Union, 6.5, 6.5.1, 6.9, 18.4; GATT Art. VI", "respondent": "Russia", "third_parties": [], "agreements": ["ADA Arts. 1, 3.1, 3.2, 3.4, 3.5, 4.1,"], "articles": [], "subject": "The Russian Federation’s imposition of anti-dumping duties on certain light commercial vehicles from Germany and Italy pursuant to a Decision of the Board of the Eurasian Economic Commission (EEC), in", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 4.1 (definition of domestic industry): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 4.1 by not including GAZ, a domestic producer of the like product, in its definition of “domestic industry” solely on the basis that it had furnished allegedly deficient data. • ADA Arts. 3.1 and 3.2 (price suppression): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 3.2 by failing to take into account the impact of the financial crisis in determining the rate of return used to construct the target domestic price for its price suppression analysis. However, the Appellate Body reversed the Panel’s finding that the evidence on the investigation record did not require the DIMD to examine whether the market could absorb further price increases. • DSU Art. 11 and ADA Art. 17.6 (confidential report): The Appellate Body reversed the Panel’s findings concerning three injury factors und", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS483", "title": "CHINA – CELLULOSE PULP", "complainant": "Canada", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4 and 3.5"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.2 (injury determination – volume of dumped imports): The Panel found that China did not act inconsistently with Arts. 3.1 and 3.2 in not assessing the significance of an absolute increase in dumped imports in light of the factual circumstances in the market such as domestic demand, volume of domestic like product and non-dumped imports. The Panel highlighted the separate nature of the inquiries set out in Art. 3.2 and considered that while the principle in Art. 3.1 that an injury determination must be based on an objective examination of positive evidence applies generally to the consideration of increased imports under Art. 3.2, it does not inform the substance of that consideration. The Panel also found China’s consideration of the price effects was inconsistent with Arts. 3.1 and 3.2 of the Anti-Dumping Agreement because MOFCOM (i) failed to explain the role of those parallel price trends between dumped import and domestic like product prices in the decline of ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS485", "title": "RUSSIA – TARIFF TREATMENT", "complainant": "European Union", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Arts. II:1(a) and II:1(b)"], "articles": [], "subject": "", "sector": "Other", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1(b) (schedules of concessions): The Panel found that a measure can be found to be inconsistent with Art. II:1(b), first sentence, on the basis of its design and structure, and that it is not necessary to provide evidence of actual transactions or adverse trade effects. The Panel also found that Art. II:1(b), first sentence, prohibits Members from exceeding their tariff bindings by even de minimis amounts. Finally, the Panel confirmed that Members cannot balance less favourable tariff treatment of some imports against more favourable treatment of others. Thus, a Member may not impose customs duties in excess of bound rates for some imports even if it imposes customs duties below bound rates for others. The Panel found that the first to sixth measures at issue were inconsistent with Art. II:1(b), first sentence, because they resulted in the imposition of customs duties in excess of Russia's bound rates. The Panel also found that the seventh to eleventh measures were incon", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS487", "title": "US – TAX INCENTIVES", "complainant": "European Union, 3.2", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1(a)(1)(ii), 1.1(b), 3.1(b),"], "articles": [], "subject": "Legislation enacted in the state of Washington in the United States that amended and extended tax incentives for the aerospace industry.", "sector": "Subsidies & Anti-Subsidy", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ASCM Art. 1 (definition of a subsidy): The Panel found that the tax rate, credit or exemption at issue for each of the challenged measures constituted a financial contribution under Art. 1.1(a)(1)(ii) because (i) government revenue that is otherwise due is foregone or not collected, and (ii) a benefit within the meaning of Art. 1.1(b) is thereby conferred. It thus concluded that each of the measures constituted a subsidy under Art. 1. • ASCM Art. 3 (prohibited subsidies – import substitution subsidies): The Appellate Body upheld the Panel’s finding that the siting provisions challenged by the European Union, considered either individually or together, did not violate Art. 3.1 because the European Union did not demonstrate that these measures, on their own, and based on their express terms, made the challenged aerospace tax measures de jure contingent upon the use of domestic over imported goods. The Appellate Body reversed the Panel’s finding that one of the challenged measures (the ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS492", "title": "EU – POULTRY MEAT (CHINA)", "complainant": "China, XXVIII:1, XXVIII:2", "respondent": "European Union", "third_parties": [], "agreements": ["GATT Arts. I:1, II:1, XIII:1, XIII:2, XIII:4"], "articles": [], "subject": "The modification by the European Union of tariff concessions on certain poultry products pursuant to negotiations held under GATT Art. XXVIII, and certain instruments implementing such modifications a", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2017", "summary_ar": "", "summary_en": "• GATT Art. XXVIII (modification of schedules): The Panel found that the European Union had not acted inconsistently with Art. XXVIII:1 by not recognizing China as a Member holding a principal or substantial supplying interest in the concessions at issue because (i) it was not obliged to take into account the SPS measures that restricted Chinese poultry imports over the relevant reference periods since they were not “discriminatory quantitative restrictions”; and (ii) it was not obliged to re-determine which Members held a substantial supplying interest based on changes in import shares after the initiation of the negotiations. The Panel found that the European Union had not acted inconsistently with Art. XXVIII:2 regarding the total amount of the TRQs, because (i) it was not obliged to calculate such amount based either on an estimate of import levels in the absence of the SPS measures, or of import levels over the three years preceding the conclusion of the negotiations; and (ii) Art", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS511", "title": "CHINA – AGRICULTURAL PRODUCERS", "complainant": "United States, 6.3 and 7.2", "respondent": "China", "third_parties": [], "agreements": [], "articles": [], "subject": "China’s provision for domestic support, in the form of market price support, in excess of its product specific de minimis level, provided to agricultural producers of various products in 2012, 2013, 2", "sector": "Agriculture & Food", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2019", "summary_ar": "", "summary_en": "• AA Arts. 3.2 and 6.3 (domestic support commitments): The Panel found that China provided domestic support, in terms of its Current Total Aggregate Measurement(s) of Support (AMS), in the form of market price support to the producers of certain agricultural products in excess of its commitment level of “nil”, set forth in Section I of Part IV of China’s Schedule of Concessions on Goods CLII, in violation of Arts. 3.2 and 6.3. • AA Art. 7.2(b) (prohibition of domestic support to agricultural producers in excess of the relevant de minimis level): Having found that China had acted inconsistently with Arts. 3.2 and 6.3 of the AA, the Panel did not find it necessary to conduct an assessment of the alternative claim under Art. 7.2(b).", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS512", "title": "RUSSIA – TRAFFIC IN TRANSIT", "complainant": "Ukraine, Accession", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Art. XX1(b), Russia’s Protocol of"], "articles": [], "subject": "", "sector": "Other", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2019", "summary_ar": "", "summary_en": "• GATT 1994 Art. XXI(b)(iii) (national security exception not totally self-judging – measures taken in an emergency in international relations): The Panel interpreted Art. XXI(b) as vesting in panels the power to review whether the requirements of the enumerated subparagraphs were met, rather than leaving it to the unfettered discretion of the invoking Member. Accordingly, the Panel rejected the Russian Federation’s argument that the Panel lacked jurisdiction to review the Russian Federation’s invocation of Art. XXI(b)(iii). The Panel considered that an “emergency in international relations” referred generally to a situation of armed conflict, or of latent armed conflict, or of heightened tension or crisis, or of general instability engulfing and surrounding a state. Both the existence of an “emergency in international relations” and whether the action was “taken in time of” such emergency, within the meaning of subparagraph (iii) of Art. XXI(b), were subject to objective determination", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS513", "title": "MOROCCO – HOT-ROLLED STEEL (TURKEY)", "complainant": "Turkey", "respondent": "Morocco", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.4, 5.10, 6.8, 6.9"], "articles": [], "subject": "Definitive anti-dumping measures imposed by Morocco on imports from, among others, Turkey.", "sector": "Metals & Mining", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 5.10 (time-limit for conclusion of investigation): The Panel found that Morocco had acted inconsistently with Art. 5.10 by failing to conclude the investigation within the 18-month maximum time limit set out in that provision. • ADA Art. 3.1 (injury determination – establishment of domestic industry): The Panel found that Morocco had acted inconsistently with Art.3.1 in determining that the domestic industry was “unestablished”. • ADA Arts. 3.1 and 3.4 (injury determination): The Panel found that Morocco had acted inconsistently with Arts. 3.1 and 3.4 by improperly conducting the injury analysis in the form of “material retardation of the establishment of the domestic industry”. The Panel found that the investigating authority had (i) failed to evaluate five of the 15 injury factors listed in Art 3.4; (ii) disregarded the captive market in the injury analysis; and (iii) relied in the injury analysis on a particular report without properly investigating the significance of in", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS529", "title": "AUSTRALIA – ANTI-DUMPING MEASURES ON PAPER", "complainant": "Indonesia", "respondent": "Australia", "third_parties": [], "agreements": ["ADA Arts. 2.2, 2.2.1.1, 9.3"], "articles": [], "subject": "Anti-dumping measure imposed on imports from Indonesia following an anti-dumping investigation by the Australian Anti-Dumping Commission (ADC).", "sector": "Anti-Dumping", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 2.2: (dumping determination – particular market situation): Prior to this Panel, no panel or AB report had interpreted the phrase “particular market situation” as it appears in Art. 2.2, which provides for the discarding of domestic sales as the basis for normal value when “because of a particular market situation … such sales do not permit a proper comparison”. 2 The Panel found that a “particular market situation” is only relevant insofar as it has the effect of rendering domestic sales unfit to permit a proper comparison, and further found that the phrase does not lend itself to a definition that foresees all the varied situations that an investigating authority may encounter that would fail to permit a “proper comparison”. The Panel found that a fact-specific and case-by-case analysis was necessarily called for. On this basis, the Panel did not accept Indonesia’s position that the phrase necessarily excludes: (i) situations where input costs of the product are allegedly ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS316", "title": "EC AND CERTAIN MEMBER STATES – LARGE CIVIL AIRCRAFT", "complainant": "United States", "respondent": "European Union", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 5, 6.3, 7.8"], "articles": [], "subject": "Launch Aid/Member State Financing (LA/MSF) provided by France, German, Spain and the United Kingdom for the Airbus A350XWB and A380 LCA models that was found to have caused adverse effects in the orig", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "ASCM Art. 7.8 (remove adverse effects or withdraw the subsidy): • A380 LA/MSF: The Panel rejected the European Union's argument that amendments to the French, German, Spanish and UK A380 LA/MSF agreements achieved the withdrawal of the subsidy for purposes of Art. 7.8. The Panel concluded that the European Union failed to demonstrate that a commercial lender, faced with the likely termination of the A380 programme, would have entered into the A380 LA/MSF amendments on the terms agreed between Airbus and the relevant member State governments. The Panel also rejected that the Spanish A380 LA/MSF subsidy had been withdrawn as a result of the alleged amortization of the pre-existing subsidy, or that Airbus' announcement to terminate the A380 programme by 2021 achieved the withdrawal of the A380 LA/MSF subsidies. • A350 LA/MSF: The Panel rejected the European Union's argument that modifications to the German A350XWB LA/MSF agreement meant that the pre-existing subsidy had been replaced by a", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS371", "title": "THAILAND – CIGARETTES (PHILIPPINES) (ARTICLE 21.5 – PHILIPPINES II)", "complainant": "Philippines", "respondent": "Thailand", "third_parties": [], "agreements": ["CVA Arts. 1, 6, 7"], "articles": [], "subject": "Two sets of measures, including: (i) a set of criminal charges filed in 2017 accusing the importer of underdeclaring the customs values for 780 entries of cigarettes between 2002-2003; and (ii) 1,052 ", "sector": "Other", "year": 2018, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2018", "summary_ar": "", "summary_en": "• CVA Art. 1.1 and 1.2(a) (valuation in a related-party transaction): The Charges violated Art. 1.1 and/or the substantive obligation in Art. 1.2(a), second sentence, of the CVA by rejecting the importer's declared transaction values without conducting a proper examination of the circumstances surrounding the sale, and/or a proper determination of the price actually paid or payable. • CVA Art. 6 and 7 (valuation based on computed value / reasonable means): The Charges violated Art. 6.1 and/or Art. 7.1 of the CVA by improperly relied on pricing and cost information reported by the manufacturer in certain tax forms to determine the revised customs value of the imported goods. • CVA Arts. 2-7 (sequential use of valuation methods): The Public Prosecutor violated the obligation to sequentially apply the customs valuation methods in Arts. 2 through 7 of the CVA when it determined the revised customs values of the imported goods. • GATT Art. XX (general exceptions): The general exceptions in ", "keywords": ["other", "CVA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS533", "title": "US – SOFTWOOD LUMBER VII", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 11, 14, 19.4"], "articles": [], "subject": "Countervailing measures imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Art. 14(d) (calculation of amount of subsidy – rejection of benchmarks): The Panel found that the US investigation authority (USDOC) improperly rejected as appropriate stumpage benchmarks: (i) certain private market prices in Ontario; (ii) the British Columbia Timber Sales (BCTS) auction prices; (iii) auction stumpage prices in Québec; (iv) log prices in Alberta. The Panel also found that the USDOC's use of benchmark prices from Nova Scotia was inconsistent with ASCM Art. 14(d), as the USDOC erroneously found that the Nova Scotia benchmark price reasonably reflected the prevailing market conditions in certain provinces where the good was provided. Further, the Panel found that the USDOC acted inconsistently with ASCM Art. 14(d) because it did not make necessary adjustments to the Nova Scotia benchmark price such that the benchmark price related to the prevailing market conditions in the market where the good was provided. • ASCM Arts. 14 and 19.4 and GATT Art. VI:3 (reliance on ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS534", "title": "US – DIFFERENTIAL PRICING METHODOLOGY", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2.1 and 2.4.2"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping – identification of pattern): The USDOC found “a single pattern” of export prices “which differed significantly among different purchasers, regions and time periods”. This pattern included export prices to purchasers, regions or time periods that differed significantly because they were significantly higher than export prices to other purchasers, regions or time periods. The parties disagreed on whether, as a matter of law, the pattern clause permits an investigating authority to find such a “pattern”. The Panel found that (i) in applying the differential pricing methodology (DPM), and specifically under the ratio test, the USDOC had acted inconsistently with the second sentence of ADA Art. 2.4.2 because it had aggregated differences in export prices across unrelated categories, i.e. purchasers, regions and time periods to identify a single pattern of export prices which differed significantly among different purchasers, regions and time periods; but that (ii)", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS541", "title": "INDIA – EXPORT RELATED MEASURES", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1(a), 27; Annexes"], "articles": [], "subject": "Exemptions from, or reductions of, customs duties or taxes, and granting by the government of India of freely transferable notes (scrips) to be used to satisfy certain liabilities vis-à-vis the govern", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Art. 27.2(b) (special and differential treatment of developing countries): The Panel rejected India’s argument that following its graduation from Art. 27.2(a) and Annex VII(b), the prohibition in Art. 3.1(a) still did not apply to its subsidy schemes, as a result of Art. 27.2(b). India did not fall under Art. 27.2, because (i) it had graduated from Annex VII(b) and ASCM Art. 27.2(a); and (ii) Art. 27.2(b) had expired on 1 January 2003, also for Members graduating from Annex VII(b). • ASCM footnote 1 (measures not deemed to be a subsidy): The Panel rejected India’s argument that the customs duties and excise taxes under the EOU/EHTP/BTP Schemes and the EPCG Scheme, and the MEIS scrips had to be deemed not to be subsidies in application of footnote 1. The Panel found that these measures did not meet the conditions set out in footnote 1 read together with Annexes I(g), I(h), and I(i). Some of the exemptions under the DFIS met these conditions and were deemed not to be subsidies. • ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS556", "title": "US – STEEL AND ALUMINIUM (CHINA), US – STEEL AND ALUMINIUM", "complainant": "Norway, China, Switzerland", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. I.1; II:1;"], "articles": [], "subject": "Duties and related measures imposed by the United States on steel and aluminium imports under Section 232 of the Trade Expansion Act of 1962, as amended.", "sector": "Metals & Mining", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Panels found that the duties on steel and aluminium were inconsistent with Art. II:1 as they exceeded the bound tariff rates in the United States’ WTO Schedule of Concessions. • GATT Art. I:1 (most-favoured-nation treatment): The Panels found that exemptions from the duties granted to steel and aluminium products from certain countries were inconsistent with the requirement of most-favoured-nation treatment under Art. I:1. • GATT Art. XI:1 (prohibition on quantitative restrictions): The Panels found that quotas on steel and aluminium products from certain countries were inconsistent with the requirement to eliminate quantitative restrictions under Art. XI:1 (only in DS552; DS556; DS564). • GATT Art. XXI(b)(iii) (national security exception): The Panels did not find based on the evidence and arguments submitted by the parties that the measures were “taken in time of war or other emergency in international relations”. Accordingly, the Pane", "keywords": ["metals & mining", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS553", "title": "KOREA – STAINLESS STEEL BARS", "complainant": "Japan", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 6.5, 6.8, 11.3, 11.4"], "articles": [], "subject": "Third sunset review by the Korean investigating authority (KIA) of anti-dumping duties on certain stainless steel bars (SSB) from Japan.", "sector": "Metals & Mining", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Art. 11.3 (review of anti-dumping duties – likelihood of recurrence of injury – price and volume effects): Japan argued the KIA’s conclusion that “it is highly likely that once the anti-dumping measures are terminated, a drop in the price of the product under investigation and an increase in imports will again cause material injury to the domestic industry” rested on a defective analysis of the likely consequences of the Japanese price drop. The Panel considered that (i) the KIA had failed to engage in an unbiased and objective evaluation of the facts when concluding that domestic price competitiveness would be weakened by the Japanese pricing level resulting from the removal of the anti-dumping duty from the average Japanese resale price; and that (ii) by failing to address how the significantly higher-priced Japanese imports could increase in a price-sensitive market, the KIA’s determination had failed to resolve a tension in its own findings, and accordingly, it did not reflec", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS567", "title": "SAUDI ARABIA – PROTECTION OF IPRS", "complainant": "Qatar", "respondent": "Saudi Arabia", "third_parties": [], "agreements": ["TRIPS Arts. 3.1, 4, 9, 14.3, 16.1, 41.1,"], "articles": [], "subject": "Measures relating to the piracy by beoutQ, a broadcasting entity, of the proprietary content of beIN, a global sports and entertainment company headquartered in Qatar. 2. SUMMARY OF KEY PANEL FINDINGS", "sector": "Intellectual Property", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "HIGH", "saudi_impact": "تأثير مباشر على مصالح المملكة", "request_date": "2018", "summary_ar": "", "summary_en": "• Panel’s jurisdiction (DSU Arts. 3.4, 3.7 and 11): The Panel found that it could not decline to exercise its jurisdiction over the claims of WTO-inconsistency that fell within its terms of reference and that the matter was justiciable. • TRIPS Arts. 41.1 (general obligations) and 42 (civil and administrative procedures and remedies): The Panel found that Saudi Arabia had acted inconsistently with TRIPS Art. 42 by taking measures that, directly or indirectly, had had the result of preventing beIN from obtaining Saudi legal counsel to enforce its IP rights through civil enforcement procedures before Saudi courts and tribunals (i.e. anti-sympathy measures). The Panel also considered that this violation of TRIPS Art. 42 had given rise to a consequential violation by Saudi Arabia of the obligation under TRIPS Art. 41 to “ensure that enforcement procedures as specified in this Part are available under their law”. • TRIPS Art. 61 (criminal procedures): The Panel found that Saudi Arabia had a", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS592", "title": "INDONESIA – RAW MATERIALS", "complainant": "European Union", "respondent": "Indonesia", "third_parties": [], "agreements": ["GATT Arts. XI, XI:2(a), XX(d)"], "articles": [], "subject": "A prohibition on the exportation of nickel ore (export ban) and a domestic processing requirement (DPR) whereby all nickel ore had to be processed (purified or refined) in Indonesia.", "sector": "Other", "year": 2021, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2021", "summary_ar": "", "summary_en": "• GATT Arts. XI:1 and XI:2(a) (quantitative restrictions): The Panel first considered whether the challenged measures fell within the scope of Art. XI. The Panel found that the export ban was a prohibition on the export of nickel ore. With respect to the DPR, the Panel found that it was a restriction within the meaning of Art. XI:1 even though it applied to all domestic actors irrespective of the destination of their goods. The Panel reasoned that because Art. XI:1 also covers measures prohibiting or restricting “sale for export” it applied to domestic regulations that prevent or limit the ability to sell goods for export. The Panel found that because domestic processing transforms nickel ore into another product, by requiring domestic processing prior to export, the DPR by its nature restricted the sale for export of nickel ore. The Panel concluded, therefore, that both measures were covered by the obligation in Art. XI:1. • GATT Art. XI:2(a) (prohibition on quantitative restrictions ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS597", "title": "US – ORIGIN MARKING (HONG KONG, CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. I:1, IX:1", "ROA Arts. 2(c), 2(d)", "TBT Art. 2.1"], "articles": [], "subject": "Requirement applied by the United States that imported goods produced in Hong Kong, China may no longer be marked to indicate “Hong Kong” as their origin, but must be marked to indicate “China” (origi", "sector": "Standards & TBT", "year": 2021, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2021", "summary_ar": "", "summary_en": "• GATT Art. XXI(b) (self-judging nature of Art. XXI(b)(iii)): The Panel examined the ordinary meaning of Art. XXI(b), focusing on the grammatical structure of the provision in the three authentic languages, and found that the phrase “which it considers” in the chapeau of Article XXI(b) does not extend to the subparagraphs following the chapeau. The Panel tested this meaning against the context of Art. XXI(b) and the object and purpose of the covered agreements and confirmed that it made sense. It concluded that Art. XXI(b) was only partly self-judging in that the subparagraphs were not subject solely to the invoking Member’s own determination, but were, instead, subject to review by a panel. The Panel thus rejected the United States’ request to (only) find that the United States had invoked its essential security interests and to so report to the DSB. Instead, the Panel proceeded to examine whether the United States had breached its obligation under GATT Art. IX:1. • GATT Art. IX:1: Th", "keywords": ["standards & tbt", "GATT", "ROA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}]
# ══════════════════════════════════════════════════════════════════════════════
# COMBINED DATASET
# ══════════════════════════════════════════════════════════════════════════════
def build_combined():
    combined = {}
    for d in WTO_PDF_DISPUTES:
        combined[d['ds_number']] = d
    for d in WTO_SAUDI_CASES:
        combined[d['ds_number']] = d
    return list(combined.values())

WTO_ALL_DISPUTES = build_combined()

# ══════════════════════════════════════════════════════════════════════════════
# MCP SERVER METADATA — WTO Dispute Settlement MCP Server
# ══════════════════════════════════════════════════════════════════════════════
MCP_SERVER_INFO = {
    "name": "WTO Dispute Settlement MCP Server",
    "version": "1.0.0",
    "description": "Read-only MCP server for WTO dispute settlement data analysis",
    "mode": "read-only",
    "data_source": "WTO One-Page Case Summaries 1995-2022 + Saudi Curated Dataset",
    "tools": [
        {"name": "search_disputes", "description": "Search WTO disputes by country, year, agreement, sector, subject or DS number"},
        {"name": "get_dispute_details", "description": "Get full details of a specific dispute (DSxxx)"},
        {"name": "get_dispute_documents", "description": "Get official WTO document links for a dispute"},
        {"name": "extract_legal_claims", "description": "Extract agreements and legal articles from a dispute"},
        {"name": "get_case_timeline", "description": "Build procedural timeline for a dispute"},
        {"name": "find_similar_disputes", "description": "Find WTO cases similar to a given dispute"},
        {"name": "analyze_saudi_relevance", "description": "Analyze how a dispute affects Saudi Arabia's trade interests"},
        {"name": "generate_legal_summary", "description": "Generate bilingual (AR/EN) executive legal summary"},
    ],
    "constraints": [
        "Read-only access to WTO official data",
        "No scraping of WTO websites",
        "Source attribution required for all data",
        "Human verification recommended before legal use"
    ]
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def build_stats():
    stats = {
        "total": len(WTO_ALL_DISPUTES),
        "total_pdf": len(WTO_PDF_DISPUTES),
        "total_saudi_curated": len(WTO_SAUDI_CASES),
        "by_year": {}, "by_sector": {}, "by_status": {}, "by_agreement": {},
        "saudi_involvement": {"direct":0,"third_party":0,"high":0,"medium":0},
        "top_complainants": {}, "top_respondents": {}
    }
    for d in WTO_ALL_DISPUTES:
        y = str(d.get("year",""))
        if y: stats["by_year"][y] = stats["by_year"].get(y,0)+1
        s = d.get("sector","Other")
        stats["by_sector"][s] = stats["by_sector"].get(s,0)+1
        st = d.get("stage",d.get("status",""))
        if st: stats["by_status"][st] = stats["by_status"].get(st,0)+1
        for ag in d.get("agreements",[]):
            k = ag.split()[0][:15] if ag else ""
            if k: stats["by_agreement"][k] = stats["by_agreement"].get(k,0)+1
        c = d.get("complainant",""); r = d.get("respondent","")
        if "Saudi Arabia" in r or "Saudi Arabia" in c: stats["saudi_involvement"]["direct"]+=1
        if "Saudi Arabia" in str(d.get("third_parties",[])): stats["saudi_involvement"]["third_party"]+=1
        if d.get("saudi_relevance")=="HIGH": stats["saudi_involvement"]["high"]+=1
        if d.get("saudi_relevance")=="MEDIUM": stats["saudi_involvement"]["medium"]+=1
        if c: stats["top_complainants"][c] = stats["top_complainants"].get(c,0)+1
        if r: stats["top_respondents"][r] = stats["top_respondents"].get(r,0)+1
    return stats

def find_dispute(ds_number):
    ds_upper = ds_number.upper().strip()
    for d in WTO_ALL_DISPUTES:
        if d["ds_number"].upper() == ds_upper:
            return d
    return None

def ai_call(prompt, max_tokens=2000):
    if not ANTHROPIC_API_KEY or not ANTHROPIC_AVAILABLE:
        return None, "ANTHROPIC_API_KEY not configured"
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role":"user","content":prompt}]
        )
        return msg.content[0].text, None
    except Exception as e:
        return None, str(e)

def search_disputes_logic(q="", year="", agreement="", sector="", complainant="",
                          respondent="", status="", saudi_relevance="", logic="AND",
                          source="all", page=1, per_page=30):
    if source == "pdf": pool = WTO_PDF_DISPUTES
    elif source == "curated": pool = WTO_SAUDI_CASES
    else: pool = WTO_ALL_DISPUTES

    results = []
    for d in pool:
        filters = []
        if q:
            text = " ".join([
                d.get("title",""), d.get("subject",""), d.get("sector",""),
                d.get("summary_en",""), d.get("complainant",""), d.get("respondent",""),
                " ".join(d.get("keywords",[])), " ".join(d.get("agreements",[]))
            ]).lower()
            filters.append(q.lower() in text)
        if year: filters.append(str(d.get("year","")) == year)
        if agreement: filters.append(any(agreement.lower() in a.lower() for a in d.get("agreements",[])))
        if sector: filters.append(sector.lower() in d.get("sector","").lower())
        if complainant: filters.append(complainant.lower() in d.get("complainant","").lower())
        if respondent: filters.append(respondent.lower() in d.get("respondent","").lower())
        if status: filters.append(status.lower() in d.get("stage",d.get("status","")).lower())
        if saudi_relevance: filters.append(d.get("saudi_relevance","") == saudi_relevance.upper())
        if not filters: results.append(d)
        elif logic.upper() == "OR":
            if any(filters): results.append(d)
        else:
            if all(filters): results.append(d)

    total = len(results)
    start = (page-1)*per_page
    return {
        "total": total, "page": page, "per_page": per_page,
        "pages": (total+per_page-1)//per_page,
        "disputes": results[start:start+per_page],
        "source_counts": {"all":len(WTO_ALL_DISPUTES),"pdf":len(WTO_PDF_DISPUTES),"curated":len(WTO_SAUDI_CASES)}
    }

# ══════════════════════════════════════════════════════════════════════════════
# STANDARD API ROUTES
# ══════════════════════════════════════════════════════════════════════════════
INDEX_HTML_PLACEHOLDER = "INDEX_HTML_GOES_HERE"

@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"): return jsonify({"error":"Not found"}), 404
    return Response(INDEX_HTML, mimetype="text/html")

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error":"Server error","detail":str(e)}), 500

@app.route("/api/health")
def health():
    return jsonify({
        "status":"ok","version":"3.0.0",
        "platform":"WTO Dispute Intelligence Platform",
        "total_disputes":len(WTO_ALL_DISPUTES),
        "pdf_disputes":len(WTO_PDF_DISPUTES),
        "saudi_curated":len(WTO_SAUDI_CASES),
        "ai_enabled":bool(ANTHROPIC_API_KEY and ANTHROPIC_AVAILABLE),
        "mcp_server":"WTO Dispute Settlement MCP Server v1.0",
        "timestamp":datetime.utcnow().isoformat()
    })

@app.route("/api/disputes")
def get_disputes():
    return jsonify(search_disputes_logic(
        q=request.args.get("q",""),
        year=request.args.get("year",""),
        agreement=request.args.get("agreement",""),
        sector=request.args.get("sector",""),
        complainant=request.args.get("complainant",""),
        respondent=request.args.get("respondent",""),
        status=request.args.get("status",""),
        saudi_relevance=request.args.get("saudi_relevance",""),
        logic=request.args.get("logic","AND"),
        source=request.args.get("source","all"),
        page=int(request.args.get("page",1)),
        per_page=int(request.args.get("per_page",30))
    ))

@app.route("/api/disputes/<ds_number>")
def get_dispute(ds_number):
    d = find_dispute(ds_number)
    if not d: return jsonify({"error":"Not found"}), 404
    return jsonify(d)

@app.route("/api/stats")
def get_stats():
    return jsonify(build_stats())

@app.route("/api/saudi-watch")
def saudi_watch():
    cases = [d for d in WTO_ALL_DISPUTES
             if d.get("complainant","")=="Saudi Arabia"
             or d.get("respondent","")=="Saudi Arabia"
             or "Saudi Arabia" in str(d.get("third_parties",[]))
             or d.get("saudi_relevance") in ["HIGH","MEDIUM"]]
    cases.sort(key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("saudi_relevance","LOW"),3))
    return jsonify({"total":len(cases),"disputes":cases})

@app.route("/api/parties")
def get_parties():
    bad = {"2.","AGREEMENT","N/A","","غير محدد","Respondent","1.","3."}
    complainants, respondents = set(), set()
    for d in WTO_ALL_DISPUTES:
        for c in d.get("complainant","").split(","):
            c = c.strip()
            if c and c not in bad and len(c)>2: complainants.add(c)
        r = d.get("respondent","").strip()
        if r and r not in bad and len(r)>2: respondents.add(r)
    return jsonify({"complainants":sorted(complainants),"respondents":sorted(respondents),"all":sorted(complainants|respondents)})

# ══════════════════════════════════════════════════════════════════════════════
# MCP TOOL ROUTES — WTO Dispute Settlement MCP Server
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/mcp/info")
def mcp_info():
    """MCP Server manifest"""
    return jsonify(MCP_SERVER_INFO)

@app.route("/api/mcp/search_disputes", methods=["POST","GET"])
def mcp_search_disputes():
    """MCP Tool: search_disputes — Search WTO cases by multiple criteria"""
    p = request.get_json(silent=True) or request.args.to_dict()
    result = search_disputes_logic(
        q=p.get("query",""),
        year=p.get("year",""),
        agreement=p.get("agreement",""),
        sector=p.get("sector",""),
        complainant=p.get("complainant",""),
        respondent=p.get("respondent",""),
        status=p.get("status",""),
        saudi_relevance=p.get("saudi_relevance",""),
        logic=p.get("logic","AND"),
        page=int(p.get("page",1)),
        per_page=int(p.get("per_page",20))
    )
    return jsonify({
        "tool": "search_disputes",
        "source": "WTO One-Page Case Summaries 1995-2022 + Saudi Curated Dataset",
        "source_url": "https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm",
        "retrieved_at": datetime.utcnow().isoformat(),
        "confidence": "HIGH",
        "result": result
    })

@app.route("/api/mcp/get_dispute_details", methods=["POST","GET"])
def mcp_get_dispute_details():
    """MCP Tool: get_dispute_details — Full details of DS case"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = p.get("ds_number","")
    if not ds_num: return jsonify({"error":"ds_number required"}), 400
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    return jsonify({
        "tool": "get_dispute_details",
        "ds_number": ds_num,
        "source_url": f"https://www.wto.org/english/tratop_e/dispu_e/cases_e/{ds_num.lower()}_e.htm",
        "retrieved_at": datetime.utcnow().isoformat(),
        "confidence": "HIGH",
        "result": d
    })

@app.route("/api/mcp/get_dispute_documents", methods=["POST","GET"])
def mcp_get_dispute_documents():
    """MCP Tool: get_dispute_documents — Official WTO document links"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = (p.get("ds_number","") or "").upper()
    if not ds_num: return jsonify({"error":"ds_number required"}), 400
    d = find_dispute(ds_num)
    ds_lower = ds_num.lower()
    wt_code = ds_num.replace("DS","WT/DS")
    docs = [
        {"type":"Case Page","url":f"https://www.wto.org/english/tratop_e/dispu_e/cases_e/{ds_lower}_e.htm","description":"Main WTO case page"},
        {"type":"Documents Search","url":f"https://docs.wto.org/dol2fe/Pages/SS/directdoc.aspx?filename=q:/WT/DS/{ds_num.replace('DS','')}.pdf","description":"Primary documents"},
        {"type":"WTO Docs Online","url":f"https://docs.wto.org/dol2fe/Pages/FE_Search/FE_S_S009-DP.aspx?language=E&CatalogueIdList=&CurrentCatalogueIdIndex=0&FullTextHash=371857150&HasEnglishRecord=True&HasFrenchRecord=True&HasSpanishRecord=True","description":"Search WTO Documents Online"},
        {"type":"Panel Report","url":f"https://docs.wto.org/dol2fe/Pages/SS/directdoc.aspx?filename=q:/WT/DS/{ds_num.replace('DS','')}/R.pdf","description":"Panel Report"},
        {"type":"AB Report","url":f"https://docs.wto.org/dol2fe/Pages/SS/directdoc.aspx?filename=q:/WT/DS/{ds_num.replace('DS','')}/AB-R.pdf","description":"Appellate Body Report"},
    ]
    if d:
        docs.insert(0, {"type":"Case Summary","url":d.get("source",""),"description":f"Official WTO summary for {ds_num}"})
    return jsonify({
        "tool":"get_dispute_documents","ds_number":ds_num,
        "wt_code":wt_code,"documents":docs,
        "disclaimer":"Links are constructed from WTO URL patterns — verify availability on docs.wto.org",
        "retrieved_at":datetime.utcnow().isoformat()
    })

@app.route("/api/mcp/extract_legal_claims", methods=["POST","GET"])
def mcp_extract_legal_claims():
    """MCP Tool: extract_legal_claims — Agreements and articles from a dispute"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = p.get("ds_number","")
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    ag_detail = []
    for ag in d.get("agreements",[]):
        parts = ag.split()
        code = parts[0] if parts else ag
        arts = " ".join(parts[1:]) if len(parts)>1 else ""
        full_name = {
            "GATT":"General Agreement on Tariffs and Trade 1994",
            "GATS":"General Agreement on Trade in Services",
            "TRIPS":"Agreement on Trade-Related Aspects of Intellectual Property Rights",
            "SPS":"Agreement on the Application of Sanitary and Phytosanitary Measures",
            "TBT":"Agreement on Technical Barriers to Trade",
            "SCM":"Agreement on Subsidies and Countervailing Measures",
            "ASCM":"Agreement on Subsidies and Countervailing Measures",
            "ADA":"Agreement on Implementation of Article VI of GATT 1994",
            "SA":"Agreement on Safeguards",
            "DSU":"Understanding on Rules and Procedures Governing the Settlement of Disputes",
            "TRIMs":"Agreement on Trade-Related Investment Measures",
            "ATC":"Agreement on Textiles and Clothing",
            "AA":"Agreement on Agriculture",
        }.get(code, code)
        ag_detail.append({"code":code,"full_name":full_name,"articles":arts,"raw":ag})
    return jsonify({
        "tool":"extract_legal_claims","ds_number":ds_num,
        "title":d.get("title",""),"complainant":d.get("complainant",""),
        "respondent":d.get("respondent",""),
        "agreements":ag_detail,
        "summary_extract":d.get("summary_en","")[:500],
        "source":d.get("source","WTO Official"),"retrieved_at":datetime.utcnow().isoformat()
    })

@app.route("/api/mcp/get_case_timeline", methods=["POST","GET"])
def mcp_get_case_timeline():
    """MCP Tool: get_case_timeline — Procedural timeline for a dispute"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = p.get("ds_number","")
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    year = d.get("year", "N/A")
    stage = d.get("stage","Completed")
    stages_map = {
        "Consultations": ["Consultations requested"],
        "Panel": ["Consultations requested","Panel established"],
        "Appeal": ["Consultations requested","Panel established","Panel report circulated","Appeal filed"],
        "Compliance": ["Consultations requested","Panel established","Panel report circulated","AB report circulated","DSB ruling adopted","Compliance period set"],
        "Completed": ["Consultations requested","Panel established","Panel report circulated","AB report circulated","DSB ruling adopted","Implementation completed"],
    }
    stage_key = next((k for k in stages_map if k.lower() in stage.lower()), "Completed")
    timeline = []
    for i, step in enumerate(stages_map[stage_key]):
        timeline.append({
            "step": i+1, "event": step,
            "year": year if i==0 else "~"+str(int(str(year))+i) if str(year).isdigit() else "N/A",
            "status": "completed" if i < len(stages_map[stage_key])-1 else "current",
            "wto_articles": {"Consultations requested":"DSU Art. 4","Panel established":"DSU Art. 6","Panel report circulated":"DSU Art. 12","AB report circulated":"DSU Art. 17","DSB ruling adopted":"DSU Art. 16","Compliance period set":"DSU Art. 21.3","Implementation completed":"DSU Art. 21"}.get(step,"")
        })
    return jsonify({
        "tool":"get_case_timeline","ds_number":ds_num,
        "title":d.get("title",""),"current_stage":stage,
        "timeline":timeline,"source":"WTO DSU Framework + Case Data",
        "retrieved_at":datetime.utcnow().isoformat()
    })

@app.route("/api/mcp/find_similar_disputes", methods=["POST","GET"])
def mcp_find_similar_disputes():
    """MCP Tool: find_similar_disputes — Cases similar to a given dispute"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = p.get("ds_number",""); limit = int(p.get("limit",5))
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    target_ags = set(a.split()[0] for a in d.get("agreements",[]))
    target_sector = d.get("sector","")
    scored = []
    for other in WTO_ALL_DISPUTES:
        if other["ds_number"] == ds_num: continue
        score = 0
        other_ags = set(a.split()[0] for a in other.get("agreements",[]))
        score += len(target_ags & other_ags) * 3
        if other.get("sector","") == target_sector: score += 2
        if other.get("respondent","") == d.get("respondent",""): score += 1
        if abs((other.get("year",0) or 0) - (d.get("year",0) or 0)) <= 5: score += 1
        if score > 0: scored.append((score, other))
    scored.sort(key=lambda x: -x[0])
    similar = [{"ds_number":x["ds_number"],"title":x["title"],"similarity_score":s,
                "shared_agreements":list(target_ags & set(a.split()[0] for a in x.get("agreements",[])))
                } for s,x in scored[:limit]]
    return jsonify({
        "tool":"find_similar_disputes","ds_number":ds_num,
        "reference_title":d.get("title",""),"similar_cases":similar,
        "methodology":"Agreement overlap + sector + respondent + year proximity",
        "retrieved_at":datetime.utcnow().isoformat()
    })

@app.route("/api/mcp/analyze_saudi_relevance", methods=["POST","GET"])
def mcp_analyze_saudi_relevance():
    """MCP Tool: analyze_saudi_relevance — Saudi Arabia trade interest analysis"""
    p = request.get_json(silent=True) or request.args.to_dict()
    ds_num = p.get("ds_number","")
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    sector = d.get("sector","")
    title_lower = d.get("title","").lower()
    summary_lower = d.get("summary_en","").lower()
    all_text = title_lower + " " + summary_lower + " " + " ".join(d.get("agreements",[]))
    analysis = {
        "saudi_relevance_level": d.get("saudi_relevance","LOW"),
        "direct_party": "Saudi Arabia" in d.get("complainant","") or "Saudi Arabia" in d.get("respondent",""),
        "third_party": "Saudi Arabia" in str(d.get("third_parties",[])),
        "sector_impact": sector,
        "affected_industries": [],
        "trade_implications": [],
        "risk_level": "LOW",
        "opportunity": False
    }
    industry_map = {
        "Energy & Environment": ["Oil & Gas","Petrochemicals","ARAMCO exports","Energy sector"],
        "Metals & Mining": ["HADEED Steel","ALBA Aluminium","Ma'aden Mining","SABIC metals"],
        "Subsidies & Anti-Subsidy": ["Saudi industrial subsidies","SIDF programs","Vision 2030 incentives"],
        "Anti-Dumping": ["Saudi chemical exports","Fertilizer exports","Petrochemical anti-dumping"],
        "Agriculture & Food": ["Saudi food imports","Food security","Agricultural trade policy"],
        "Intellectual Property": ["Saudi IP framework","SAIP enforcement"],
        "Services": ["Saudi service sector","Banking","Fintech","Logistics"],
        "Safeguards": ["Saudi industrial protection","Manufacturing sector"],
    }
    analysis["affected_industries"] = industry_map.get(sector, ["General trade"])
    cbam_relevant = any(x in all_text for x in ["cbam","carbon border","carbon tax","emission"])
    if cbam_relevant:
        analysis["trade_implications"].append("CBAM may impose carbon costs on Saudi exports to EU")
        analysis["risk_level"] = "HIGH"
    steel_relevant = any(x in all_text for x in ["steel","aluminum","aluminium","metal"])
    if steel_relevant:
        analysis["trade_implications"].append("Affects Saudi steel/aluminum export competitiveness")
        if analysis["risk_level"] == "LOW": analysis["risk_level"] = "MEDIUM"
    subsidy_relevant = any(x in all_text for x in ["subsidy","subsidies","countervailing"])
    if subsidy_relevant:
        analysis["trade_implications"].append("Sets precedent for industrial subsidy programs under Vision 2030")
        if analysis["risk_level"] == "LOW": analysis["risk_level"] = "MEDIUM"
    if d.get("saudi_relevance") == "HIGH":
        analysis["risk_level"] = "HIGH"
        analysis["opportunity"] = d.get("respondent","") not in ["Saudi Arabia"]
    return jsonify({
        "tool":"analyze_saudi_relevance","ds_number":ds_num,
        "title":d.get("title",""),"analysis":analysis,
        "saudi_impact_description":d.get("saudi_impact",""),
        "recommendation":"Monitor closely" if analysis["risk_level"]=="HIGH" else ("Track developments" if analysis["risk_level"]=="MEDIUM" else "No immediate action required"),
        "retrieved_at":datetime.utcnow().isoformat()
    })

@app.route("/api/mcp/generate_legal_summary", methods=["POST"])
def mcp_generate_legal_summary():
    """MCP Tool: generate_legal_summary — AI-powered bilingual legal summary"""
    p = request.get_json(silent=True) or {}
    ds_num = p.get("ds_number",""); lang = p.get("language","both")
    d = find_dispute(ds_num)
    if not d: return jsonify({"error":f"{ds_num} not found"}), 404
    if not ANTHROPIC_API_KEY:
        return jsonify({"error":"ANTHROPIC_API_KEY required for AI summary","tool":"generate_legal_summary"}), 503
    prompt = f"""You are a senior WTO Legal Advisor. Generate a professional bilingual summary.

Dispute: {d['ds_number']} — {d['title']}
Complainant: {d.get('complainant','')} | Respondent: {d.get('respondent','')}
Agreements: {', '.join(d.get('agreements',[]))}
Stage: {d.get('stage','')} | Sector: {d.get('sector','')}
Saudi Relevance: {d.get('saudi_relevance','')} — {d.get('saudi_impact','')}
Summary: {d.get('summary_en','')[:600]}

Provide:
1. ARABIC SUMMARY (3-4 sentences, professional legal Arabic)
2. ENGLISH SUMMARY (3-4 sentences)
3. KEY LEGAL ISSUES (2-3 bullet points)
4. SAUDI ARABIA IMPLICATIONS (2-3 bullet points)

Format with clear section headers."""
    text, err = ai_call(prompt, 1500)
    if err: return jsonify({"error":err,"tool":"generate_legal_summary"}), 503
    return jsonify({
        "tool":"generate_legal_summary","ds_number":ds_num,
        "summary":text,"language":lang,
        "source":"AI-generated based on WTO official data — verify before official use",
        "retrieved_at":datetime.utcnow().isoformat()
    })

# ══════════════════════════════════════════════════════════════════════════════
# AI ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/ai/analyze", methods=["POST"])
def ai_analyze():
    p = request.get_json() or {}
    d = find_dispute(p.get("ds_number",""))
    if not d: return jsonify({"error":"Not found"}), 404
    lang = "أجب باللغة العربية" if p.get("language","ar")=="ar" else "Respond in English"
    question = p.get("question","Provide comprehensive legal analysis including key issues, applicable WTO law, procedural stage, Saudi Arabia implications, and similar precedents.")
    prompt = f"""Senior WTO Legal Advisor analysis.

{d['ds_number']}: {d['title']}
Complainant: {d.get('complainant','')} | Respondent: {d.get('respondent','')}
Agreements: {', '.join(d.get('agreements',[]))} | Stage: {d.get('stage','')}
Saudi Relevance: {d.get('saudi_relevance','')} — {d.get('saudi_impact','')}
Summary: {d.get('summary_en','')[:500]}

Question: {question}
{lang}. Structure clearly. Cite WTO articles."""
    text, err = ai_call(prompt)
    if err: return jsonify({"error":err}), 503
    return jsonify({"analysis":text,"ds_number":d["ds_number"],"dispute":d})

@app.route("/api/ai/compare", methods=["POST"])
def ai_compare():
    p = request.get_json() or {}
    ds_list = p.get("ds_numbers",[])
    disputes = [find_dispute(x) for x in ds_list if find_dispute(x)]
    if len(disputes)<2: return jsonify({"error":"Provide at least 2 valid DS numbers"}), 400
    lang = "أجب باللغة العربية" if p.get("language","ar")=="ar" else "Respond in English"
    cases_text = "\n\n".join([f"{d['ds_number']}: {d['title']}\nComplainant: {d.get('complainant','')} | Respondent: {d.get('respondent','')}\nAgreements: {', '.join(d.get('agreements',[]))}\nStage: {d.get('stage','')} | Saudi: {d.get('saudi_relevance','')}" for d in disputes])
    prompt = f"""Compare these WTO disputes as a Senior WTO Legal Advisor:\n\n{cases_text}\n\nCompare: legal similarities/differences, WTO law, Saudi Arabia implications, precedent value.\n{lang}"""
    text, err = ai_call(prompt)
    if err: return jsonify({"error":err}), 503
    return jsonify({"comparison":text,"ds_numbers":ds_list})

@app.route("/api/ai/memo", methods=["POST"])
def ai_memo():
    p = request.get_json() or {}
    d = find_dispute(p.get("ds_number",""))
    if not d: return jsonify({"error":"Not found"}), 404
    lang_txt = "اكتب المذكرة بالعربية بالكامل" if p.get("language","ar")=="ar" else "Write in English"
    audience_txt = "لمسؤول في وزارة حكومية سعودية" if p.get("audience","government")=="government" else "for a private sector executive"
    prompt = f"""Prepare Executive Legal Memorandum {audience_txt}.

{d['ds_number']}: {d['title']}
Parties: {d.get('complainant','')} vs {d.get('respondent','')}
Agreements: {', '.join(d.get('agreements',[]))} | Stage: {d.get('stage','')}
Saudi Impact: {d.get('saudi_impact','')} | Relevance: {d.get('saudi_relevance','')}
Summary: {d.get('summary_en','')[:400]}

Sections: Executive Summary, Background, Key Legal Issues, Saudi Arabia Position, Risk Assessment, Strategic Recommendations, Next Steps, Official Sources.
{lang_txt}."""
    text, err = ai_call(prompt, 2500)
    if err: return jsonify({"error":err}), 503
    return jsonify({"memo":text,"dispute":d})

@app.route("/api/ai/risk", methods=["POST"])
def ai_risk():
    p = request.get_json() or {}
    d = find_dispute(p.get("ds_number",""))
    if not d: return jsonify({"error":"Not found"}), 404
    lang = "أجب باللغة العربية" if p.get("language","ar")=="ar" else "Respond in English"
    prompt = f"""Senior WTO Legal Risk Analyst. Extract legal and commercial risks.

{d['ds_number']}: {d['title']} | Sector: {d.get('sector','')}
Agreements: {', '.join(d.get('agreements',[]))}
Saudi Relevance: {d.get('saudi_relevance','')} — {d.get('saudi_impact','')}
Summary: {d.get('summary_en','')[:500]}

Provide structured risk analysis:
1. HIGH risks (immediate action needed)
2. MEDIUM risks (monitor closely)  
3. LOW risks (awareness only)
4. Commercial trade risks for Saudi exporters
5. Policy/compliance risks for Saudi government
6. Opportunities arising from this dispute
{lang}"""
    text, err = ai_call(prompt)
    if err: return jsonify({"error":err}), 503
    return jsonify({"risk_analysis":text,"dispute":d})

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    p = request.get_json() or {}
    messages = p.get("messages",[])
    sys = f"""Elite WTO Legal Advisor & MCP Intelligence System.

You have access to {len(WTO_ALL_DISPUTES)} WTO dispute cases (1995-2022) from official WTO publications + Saudi curated cases.
Specializations: WTO Agreements (GATT/GATS/TRIPS/DSU/SCM/TBT/SPS/ADA/Safeguards), Saudi trade law, GCC policies, Vision 2030, CBAM impacts.
MCP Tools available: search_disputes, get_dispute_details, get_dispute_documents, extract_legal_claims, get_case_timeline, find_similar_disputes, analyze_saudi_relevance, generate_legal_summary.

Always cite DS numbers, WTO articles, and official sources. Respond in user's language."""
    if not ANTHROPIC_API_KEY: return jsonify({"error":"ANTHROPIC_API_KEY required"}), 503
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1500,system=sys,messages=messages)
        return jsonify({"response":msg.content[0].text})
    except Exception as e:
        return jsonify({"error":str(e)}), 503

@app.route("/api/sources")
def official_sources():
    return jsonify({
        "wto_official":[
            {"name":"WTO Dispute Settlement","url":"https://www.wto.org/english/tratop_e/dispu_e/dispu_e.htm","use_case":"All WTO dispute cases"},
            {"name":"WTO Find Disputes","url":"https://www.wto.org/english/tratop_e/dispu_e/find_dispu_cases_e.htm","use_case":"Advanced case search"},
            {"name":"WTO Documents Online","url":"https://docs.wto.org","use_case":"Panel/AB Reports, DSB Minutes"},
            {"name":"WTO Data Portal","url":"https://data.wto.org","use_case":"Trade statistics and tariff data"},
            {"name":"WTO API Portal","url":"https://api.wto.org","use_case":"Programmatic data access"},
        ],
        "monitoring":[
            {"name":"ePing SPS/TBT","url":"https://epingalert.org","use_case":"SPS/TBT notifications affecting Saudi exports"},
            {"name":"WTO I-TIP","url":"https://i-tip.wto.org","use_case":"Trade policy measures tracker"},
            {"name":"WTO Environmental DB","url":"https://edb.wto.org","use_case":"CBAM and trade-environment measures"},
        ],
        "saudi_official":[
            {"name":"الهيئة العامة للتجارة الخارجية","url":"https://www.gaft.gov.sa","use_case":"Foreign trade policy"},
            {"name":"هيئة الخبراء — الأنظمة","url":"https://laws.boe.gov.sa","use_case":"Saudi regulations"},
            {"name":"هيئة الزكاة والجمارك","url":"https://www.zatca.gov.sa","use_case":"Customs and tariffs"},
        ],
        "mcp_server":{"name":"WTO Dispute Settlement MCP Server","endpoints":"/api/mcp/*","total_cases":len(WTO_ALL_DISPUTES)}
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


INDEX_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WTO Dispute Intelligence Platform v3 | منصة رصد النزاعات الذكية</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg0:#040c18;--bg1:#0a1628;--bg2:#0d1e35;--bg3:#122340;
  --b0:rgba(0,162,255,.1);--b1:rgba(0,162,255,.28);--b2:rgba(0,162,255,.5);
  --ab:#00a2ff;--ag:#c9a84c;--ae:#00e5a0;--ar:#ff4b4b;--ao:#ff8c42;--ap:#cc66ff;
  --t0:#e8f0fe;--t1:#8ba4c0;--t2:#445566;
  --sg:#006c35;--r:12px;--rl:18px;
  --shadow:0 8px 32px rgba(0,0,0,.4);
  --gblue:0 0 24px rgba(0,162,255,.15);
  --ggold:0 0 24px rgba(201,168,76,.15);
  --font-ar:'IBM Plex Sans Arabic',sans-serif;
  --font-la:'Space Grotesk',sans-serif;
  --font-mo:'JetBrains Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font-ar);background:var(--bg0);color:var(--t0);min-height:100vh;overflow-x:hidden;direction:rtl}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(0,100,200,.06) 0%,transparent 60%),radial-gradient(ellipse 60% 40% at 80% 80%,rgba(0,108,53,.05) 0%,transparent 60%);pointer-events:none;z-index:0}
select{background:#0d1e35!important;color:#e8f0fe!important}
select option{background:#0d1e35!important;color:#e8f0fe!important}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(0,162,255,.2);border-radius:3px}

/* HEADER */
header{position:sticky;top:0;z-index:100;background:rgba(4,12,24,.96);backdrop-filter:blur(20px);border-bottom:1px solid var(--b0);padding:0 1.5rem}
.hdr-inner{max-width:1600px;margin:0 auto;display:flex;align-items:center;height:56px;gap:1rem}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;flex-shrink:0}
.logo-em{width:36px;height:36px;background:linear-gradient(135deg,var(--sg),var(--ab));border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;font-family:var(--font-la)}
.logo-tx{display:flex;flex-direction:column;line-height:1.2}
.logo-main{font-size:13px;font-weight:700;color:var(--t0)}
.logo-sub{font-size:10px;color:var(--ab);letter-spacing:.8px;text-transform:uppercase;font-family:var(--font-la)}
nav{display:flex;gap:3px;overflow-x:auto;flex:1}
.nb{padding:5px 12px;border-radius:7px;border:1px solid transparent;background:transparent;color:var(--t1);font-family:var(--font-ar);font-size:12px;cursor:pointer;transition:all .15s;white-space:nowrap;flex-shrink:0}
.nb:hover,.nb.act{background:rgba(0,162,255,.09);border-color:var(--b1);color:var(--ab)}
.nb.sa{color:var(--ag)}.nb.sa:hover,.nb.sa.act{background:rgba(201,168,76,.09);border-color:rgba(201,168,76,.3)}
.nb.mcp{color:var(--ae)}.nb.mcp:hover,.nb.mcp.act{background:rgba(0,229,160,.09);border-color:rgba(0,229,160,.3)}
.ai-dot{width:7px;height:7px;background:var(--ae);border-radius:50%;display:inline-block;margin-left:4px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* MAIN */
main{position:relative;z-index:1;max-width:1600px;margin:0 auto;padding:1.5rem}
.sec{display:none}.sec.act{display:block}

/* HERO */
.hero{text-align:center;padding:2rem 0 1.5rem}
.badge{display:inline-flex;align-items:center;gap:5px;background:rgba(0,162,255,.08);border:1px solid rgba(0,162,255,.2);border-radius:100px;padding:3px 14px;font-size:11px;color:var(--ab);margin-bottom:1rem;letter-spacing:.8px;font-family:var(--font-la)}
.h1{font-size:clamp(1.5rem,3vw,2.4rem);font-weight:700;background:linear-gradient(120deg,#e8f0fe 0%,#00a2ff 50%,#c9a84c 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.6rem;line-height:1.3}
.hero-sub{color:var(--t1);font-size:13px;margin-bottom:1.5rem;line-height:1.7;max-width:600px;margin-inline:auto}

/* SEARCH BOX */
.sbox{background:var(--bg2);border:1px solid var(--b1);border-radius:var(--rl);padding:1.25rem;margin-bottom:1.5rem;box-shadow:var(--gblue)}
.srow{display:flex;gap:8px;margin-bottom:10px;align-items:center;flex-wrap:wrap}
.sinput{flex:1;min-width:200px;padding:9px 14px;background:rgba(255,255,255,.04);border:1px solid var(--b0);border-radius:var(--r);color:var(--t0);font-family:var(--font-ar);font-size:13px;outline:none;transition:border-color .2s;direction:rtl}
.sinput:focus{border-color:var(--ab)}
.sfilters{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-bottom:10px}
.fg label{font-size:10px;color:var(--t2);text-transform:uppercase;letter-spacing:.4px;display:block;margin-bottom:3px;font-family:var(--font-la)}
.fg select{width:100%;padding:7px 10px;background:#0d1e35;border:1px solid var(--b0);border-radius:8px;color:var(--t0);font-family:var(--font-ar);font-size:12px;outline:none;cursor:pointer;appearance:none;-webkit-appearance:none}
.fg select:focus{border-color:var(--ab)}
.srci{font-size:11px;color:var(--t2);display:flex;align-items:center;gap:5px;padding-top:4px;flex-wrap:wrap}

/* BUTTONS */
.btn{padding:8px 16px;border-radius:var(--r);border:none;font-family:var(--font-ar);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
.bp{background:var(--ab);color:#fff}.bp:hover{background:#0090e0;transform:translateY(-1px)}
.bg{background:var(--ag);color:#0a0a0a}.bg:hover{background:#b89640;transform:translateY(-1px)}
.bo{background:transparent;border:1px solid var(--b1);color:var(--ab)}.bo:hover{background:rgba(0,162,255,.08)}
.bgreen{background:var(--ae);color:#003020}.bgreen:hover{background:#00cc90}
.bpurple{background:var(--ap);color:#1a0030}.bpurple:hover{background:#bb55ff}
.bsm{padding:5px 11px;font-size:11px}
.ltog{display:flex;background:rgba(255,255,255,.04);border:1px solid var(--b0);border-radius:8px;overflow:hidden}
.ltog button{padding:6px 12px;border:none;background:transparent;color:var(--t1);font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}
.ltog button.act{background:var(--ab);color:#fff}

/* RESULTS */
.rh{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;flex-wrap:wrap;gap:8px}
.rcnt{font-size:13px;color:var(--t1)}
.rcnt strong{color:var(--ab);font-family:var(--font-mo);font-size:16px}
.dgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:1rem}

/* DISPUTE CARD */
.dc{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--rl);padding:1.25rem;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.dc::before{content:'';position:absolute;top:0;right:0;width:3px;height:100%;background:var(--ab);opacity:0;transition:opacity .2s}
.dc:hover{border-color:var(--b1);transform:translateY(-2px);box-shadow:var(--shadow)}.dc:hover::before{opacity:1}
.dc.sh::before{background:var(--ag);opacity:.6}.dc.sh{border-color:rgba(201,168,76,.2)}
.dc.selected{border-color:var(--ae)!important;box-shadow:0 0 0 2px rgba(0,229,160,.2)}
.dc.selected::before{background:var(--ae);opacity:1}
.ch{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:9px;flex-wrap:wrap}
.dsbdg{background:rgba(0,162,255,.1);border:1px solid rgba(0,162,255,.28);color:var(--ab);padding:2px 9px;border-radius:6px;font-size:11px;font-weight:600;white-space:nowrap;font-family:var(--font-mo)}
.rbdg{padding:2px 8px;border-radius:100px;font-size:10px;font-weight:700;white-space:nowrap;font-family:var(--font-la)}
.rH{background:rgba(201,168,76,.15);color:var(--ag);border:1px solid rgba(201,168,76,.3)}
.rM{background:rgba(0,229,160,.1);color:var(--ae);border:1px solid rgba(0,229,160,.3)}
.rL{background:rgba(255,255,255,.05);color:var(--t2);border:1px solid var(--b0)}
.ctitle{font-size:13px;font-weight:600;color:var(--t0);line-height:1.45;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.cparties{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:7px}
.ptag{padding:2px 8px;border-radius:6px;font-size:11px}
.ptag.c{background:rgba(255,75,75,.1);border:1px solid rgba(255,75,75,.2);color:#ff8080}
.ptag.r{background:rgba(255,140,66,.1);border:1px solid rgba(255,140,66,.2);color:var(--ao)}
.cags{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:7px}
.achip{background:rgba(0,162,255,.06);border:1px solid rgba(0,162,255,.15);color:var(--ab);padding:1px 7px;border-radius:4px;font-size:10px;font-family:var(--font-mo)}
.cft{display:flex;align-items:center;justify-content:space-between;margin-top:9px;padding-top:9px;border-top:1px solid var(--b0);flex-wrap:wrap;gap:4px}
.sbdg{padding:2px 8px;border-radius:6px;font-size:10px;font-weight:600;font-family:var(--font-la)}
.sCo{background:rgba(255,200,0,.1);color:#ffcc00;border:1px solid rgba(255,200,0,.2)}
.sPa{background:rgba(0,162,255,.1);color:var(--ab);border:1px solid rgba(0,162,255,.2)}
.sAp{background:rgba(200,0,255,.1);color:var(--ap);border:1px solid rgba(200,0,255,.2)}
.sIm{background:rgba(0,229,160,.1);color:var(--ae);border:1px solid rgba(0,229,160,.2)}
.sCl{background:rgba(255,255,255,.05);color:var(--t2);border:1px solid var(--b0)}
.sCom{background:rgba(255,140,66,.1);color:var(--ao);border:1px solid rgba(255,140,66,.2)}
.cyr{font-family:var(--font-mo);font-size:11px;color:var(--t2)}
.src-pip{padding:1px 6px;border-radius:4px;font-size:9px;font-family:var(--font-la);font-weight:600}
.src-pdf{background:rgba(0,229,160,.08);border:1px solid rgba(0,229,160,.2);color:var(--ae)}
.src-cu{background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);color:var(--ag)}
.chk-sel{display:flex;align-items:center;gap:4px;font-size:10px;color:var(--ae);margin-top:4px;cursor:pointer}

/* DASHBOARD */
.sgrid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:1.5rem}
.sc{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--rl);padding:1.25rem;text-align:center}
.sv{font-size:2rem;font-weight:700;font-family:var(--font-mo);background:linear-gradient(135deg,var(--ab),var(--ag));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1;margin-bottom:5px}
.sl{font-size:10px;color:var(--t2);font-weight:600;text-transform:uppercase;letter-spacing:.4px}
.cgrid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
.cc{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--rl);padding:1.25rem}
.ctit{font-size:12px;font-weight:700;color:var(--t1);margin-bottom:1rem}
.brow{display:grid;grid-template-columns:120px 1fr 30px;gap:8px;align-items:center;margin-bottom:7px}
.blbl{font-size:11px;color:var(--t1);direction:ltr;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.btrk{height:7px;background:rgba(255,255,255,.06);border-radius:100px;overflow:hidden}
.bfll{height:100%;border-radius:100px;background:linear-gradient(90deg,var(--ab),var(--ag));transition:width 1s ease}
.bcnt{font-family:var(--font-mo);font-size:11px;color:var(--t2);text-align:right}

/* SAUDI WATCH */
.shero{background:linear-gradient(135deg,rgba(0,108,53,.1),rgba(201,168,76,.08));border:1px solid rgba(201,168,76,.2);border-radius:var(--rl);padding:1.5rem;margin-bottom:1.5rem;text-align:center}
.sflag{display:flex;justify-content:center;gap:2px;margin-bottom:8px}
.fs{width:30px;height:5px;border-radius:3px}
.fsG{background:var(--sg)}.fsAu{background:var(--ag)}.fsW{background:rgba(255,255,255,.5)}
.sh2{font-size:1.4rem;font-weight:700;color:var(--ag);margin-bottom:4px}
.shp{font-size:12px;color:var(--t1)}
.sector-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin-bottom:1.5rem}
.scard{background:rgba(255,255,255,.03);border:1px solid var(--b0);border-radius:var(--r);padding:10px;text-align:center;cursor:pointer;transition:all .15s}
.scard:hover{border-color:var(--b1);background:rgba(0,162,255,.05)}
.scard.active-sec{border-color:var(--ab);background:rgba(0,162,255,.08)}
.scard-ico{font-size:1.5rem;margin-bottom:4px}
.scard-ttl{font-size:11px;font-weight:600;color:var(--t0);margin-bottom:2px}
.scard-cnt{font-size:10px;color:var(--t2)}

/* MCP SECTION */
.mcp-hero{background:linear-gradient(135deg,rgba(0,229,160,.06),rgba(0,162,255,.06));border:1px solid rgba(0,229,160,.2);border-radius:var(--rl);padding:1.5rem;margin-bottom:1.5rem}
.mcp-title{font-size:1.1rem;font-weight:700;color:var(--ae);margin-bottom:.4rem;display:flex;align-items:center;gap:8px}
.mcp-sub{font-size:12px;color:var(--t1);margin-bottom:1rem}
.mcp-badge{background:rgba(0,229,160,.1);border:1px solid rgba(0,229,160,.25);color:var(--ae);padding:2px 10px;border-radius:6px;font-size:10px;font-family:var(--font-la);font-weight:700}
.tools-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.tool-card{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--r);padding:12px;transition:all .2s;cursor:pointer}
.tool-card:hover{border-color:rgba(0,229,160,.3);background:rgba(0,229,160,.04)}
.tool-name{font-size:12px;font-weight:700;color:var(--ae);font-family:var(--font-mo);margin-bottom:4px}
.tool-desc{font-size:11px;color:var(--t1);line-height:1.5;margin-bottom:8px}
.tool-input{width:100%;padding:7px 10px;background:rgba(255,255,255,.04);border:1px solid var(--b0);border-radius:7px;color:var(--t0);font-family:var(--font-ar);font-size:11px;outline:none;direction:rtl;margin-bottom:6px}
.tool-input:focus{border-color:var(--ae)}
.tool-result{background:rgba(0,0,0,.2);border:1px solid var(--b0);border-radius:7px;padding:8px;font-size:11px;color:var(--t1);min-height:60px;white-space:pre-wrap;max-height:180px;overflow-y:auto;line-height:1.6;direction:ltr;text-align:left}

/* COMPARE */
.compare-bar{background:var(--bg2);border:1px solid var(--ae);border-radius:var(--r);padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:1rem;flex-wrap:wrap}
.compare-info{font-size:12px;color:var(--ae);flex:1}
.compare-chips{display:flex;gap:6px;flex-wrap:wrap}
.cchip{background:rgba(0,229,160,.1);border:1px solid rgba(0,229,160,.25);color:var(--ae);padding:3px 10px;border-radius:6px;font-size:11px;font-family:var(--font-mo);display:flex;align-items:center;gap:4px}
.cchip-x{cursor:pointer;opacity:.7}.cchip-x:hover{opacity:1}

/* WATCHLIST */
.wlist-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.witem{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--r);padding:12px;position:relative}
.witem-title{font-size:13px;font-weight:600;color:var(--t0);margin-bottom:6px}
.witem-tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px}
.wtag{padding:2px 8px;border-radius:100px;font-size:10px;background:rgba(0,162,255,.1);color:var(--ab);border:1px solid rgba(0,162,255,.2)}
.witem-del{position:absolute;top:10px;left:10px;background:none;border:none;color:var(--t2);cursor:pointer;font-size:14px}
.witem-del:hover{color:var(--ar)}

/* MODAL */
.mov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(8px);z-index:1000;overflow-y:auto;padding:1.5rem;align-items:flex-start;justify-content:center}
.mov.open{display:flex}
.modal{background:var(--bg1);border:1px solid var(--b1);border-radius:var(--rl);max-width:920px;width:100%;margin:auto;animation:mIn .25s ease;overflow:hidden}
@keyframes mIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
.mhdr{padding:1.25rem 1.5rem;border-bottom:1px solid var(--b0);background:rgba(0,162,255,.03);display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.mds{font-family:var(--font-mo);font-size:12px;color:var(--ab);margin-bottom:3px}
.mtitle{font-size:15px;font-weight:600;color:var(--t0);line-height:1.4;max-width:700px}
.mclose{background:rgba(255,255,255,.07);border:1px solid var(--b0);color:var(--t1);width:28px;height:28px;border-radius:7px;cursor:pointer;font-size:14px;flex-shrink:0;transition:all .15s}
.mclose:hover{background:rgba(255,75,75,.1);color:var(--ar)}
.mbody{padding:1.5rem}
.mtabs{display:flex;gap:2px;margin-bottom:1.25rem;border-bottom:1px solid var(--b0);overflow-x:auto}
.mtab{padding:7px 13px;border:none;background:transparent;color:var(--t1);font-family:var(--font-ar);font-size:12px;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s;white-space:nowrap}
.mtab.act{color:var(--ab);border-bottom-color:var(--ab)}
.tc{display:none}.tc.act{display:block}
.igrid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:1rem}
.ii{background:rgba(255,255,255,.03);border:1px solid var(--b0);border-radius:var(--r);padding:10px}
.ilbl{font-size:10px;color:var(--t2);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;font-family:var(--font-la)}
.ival{font-size:13px;color:var(--t0);font-weight:500}
.impbox{background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.2);border-radius:var(--r);padding:10px 14px;margin-bottom:1rem}
.imptitle{font-size:10px;color:var(--ag);font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px;font-family:var(--font-la)}
.impval{font-size:13px;color:var(--t0);line-height:1.55}
.aipanel{background:rgba(0,0,0,.2);border:1px solid var(--b0);border-radius:var(--r);padding:12px;font-size:13px;line-height:1.75;color:var(--t1);min-height:100px;white-space:pre-wrap;max-height:320px;overflow-y:auto}
/* Timeline */
.timeline{padding:.5rem 0}
.tl-item{display:flex;gap:12px;margin-bottom:14px;align-items:flex-start}
.tl-dot{width:28px;height:28px;border-radius:50%;background:rgba(0,162,255,.15);border:2px solid var(--ab);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:var(--ab);flex-shrink:0;font-family:var(--font-mo)}
.tl-dot.cur{background:var(--ab);color:#fff}
.tl-line{width:2px;background:rgba(0,162,255,.15);flex-shrink:0;margin:28px 13px 0}
.tl-content{flex:1;padding-top:4px}
.tl-event{font-size:13px;font-weight:600;color:var(--t0);margin-bottom:3px}
.tl-year{font-size:11px;color:var(--t2);font-family:var(--font-mo)}
.tl-art{font-size:11px;color:var(--ab);margin-top:2px;font-family:var(--font-mo)}

/* CHAT */
.chat-wrap{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--rl);overflow:hidden;display:flex;flex-direction:column;height:560px}
.chat-hdr{padding:10px 14px;background:rgba(0,162,255,.05);border-bottom:1px solid var(--b0);display:flex;align-items:center;gap:10px}
.av{width:32px;height:32px;background:linear-gradient(135deg,var(--ab),var(--sg));border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.chat-msgs{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:10px}
.msg{max-width:82%;border-radius:10px;padding:10px 13px;font-size:13px;line-height:1.7}
.msg.u{background:rgba(0,162,255,.1);border:1px solid rgba(0,162,255,.2);color:var(--t0);align-self:flex-end;border-bottom-right-radius:3px}
.msg.a{background:rgba(255,255,255,.04);border:1px solid var(--b0);color:var(--t1);align-self:flex-start;border-bottom-left-radius:3px;white-space:pre-wrap}
.chat-inp{padding:10px 14px;border-top:1px solid var(--b0);display:flex;gap:8px;align-items:flex-end}
.cinp{flex:1;padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid var(--b0);border-radius:var(--r);color:var(--t0);font-family:var(--font-ar);font-size:13px;outline:none;direction:rtl;resize:none}
.cinp:focus{border-color:var(--ab)}

/* SOURCES */
.srcgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-bottom:1.5rem}
.srcc{background:var(--bg2);border:1px solid var(--b0);border-radius:var(--rl);padding:12px;transition:all .2s;text-decoration:none;display:block}
.srcc:hover{border-color:var(--b1);transform:translateY(-2px)}
.srcnm{font-size:13px;font-weight:600;color:var(--ab);margin-bottom:5px}
.srcd{font-size:11px;color:var(--t1);margin-bottom:6px;line-height:1.45}
.srcu{font-size:10px;color:var(--t2);line-height:1.4;padding-top:6px;border-top:1px solid var(--b0)}
.stitle{font-size:13px;font-weight:700;color:var(--t1);margin-bottom:10px;display:flex;align-items:center;gap:6px;padding-bottom:7px;border-bottom:1px solid var(--b0)}

/* UTILS */
.spin{width:16px;height:16px;border:2px solid rgba(0,162,255,.2);border-top-color:var(--ab);border-radius:50%;animation:sp .7s linear infinite;display:inline-block}
@keyframes sp{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:3rem 2rem;color:var(--t2)}
.empty .ico{font-size:2.5rem;margin-bottom:.8rem}
.empty h3{font-size:1rem;margin-bottom:.4rem;color:var(--t1)}
.empty p{font-size:12px}
.section-h{font-size:.95rem;font-weight:700;color:var(--t0);margin-bottom:.8rem;display:flex;align-items:center;gap:6px}
.toast{position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%) translateY(60px);background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);padding:9px 20px;font-size:13px;color:var(--t0);z-index:9999;transition:transform .25s;box-shadow:var(--shadow)}
.toast.show{transform:translateX(-50%) translateY(0)}
.pgn{display:flex;align-items:center;gap:6px;justify-content:center;margin-top:1.5rem;flex-wrap:wrap}
@media(max-width:768px){main{padding:1rem}.dgrid{grid-template-columns:1fr}.cgrid2{grid-template-columns:1fr}.sgrid4{grid-template-columns:repeat(2,1fr)}.tools-grid{grid-template-columns:1fr}.sector-cards{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body>

<header>
  <div class="hdr-inner">
    <a class="logo" href="#" onclick="showSec('search')">
      <div class="logo-em">W</div>
      <div class="logo-tx">
        <span class="logo-main">WTO Intelligence v3</span>
        <span class="logo-sub">MCP + AI Platform</span>
      </div>
    </a>
    <nav>
      <button class="nb act" id="nb-search" onclick="showSec('search')">🔍 البحث</button>
      <button class="nb" id="nb-dash" onclick="showSec('dash')">📊 لوحة التحكم</button>
      <button class="nb sa" id="nb-saudi" onclick="showSec('saudi')">🇸🇦 Saudi Watch</button>
      <button class="nb mcp" id="nb-mcp" onclick="showSec('mcp')">⚡ MCP Tools<span class="ai-dot"></span></button>
      <button class="nb" id="nb-chat" onclick="showSec('chat')">🤖 المساعد AI</button>
      <button class="nb" id="nb-wlist" onclick="showSec('wlist')">🔔 القوائم المحفوظة</button>
      <button class="nb" id="nb-src" onclick="showSec('src')">📚 المصادر</button>
    </nav>
  </div>
</header>

<main>

<!-- ══ SEARCH ══ -->
<div class="sec act" id="sec-search">
  <div class="hero">
    <div class="badge">⚖️ WTO DISPUTE SETTLEMENT INTELLIGENCE — MCP POWERED</div>
    <div class="h1">منصة رصد نزاعات منظمة التجارة العالمية</div>
    <div class="hero-sub">بحث قانوني متقدم • تحليل ذكاء اصطناعي • MCP Server • متابعة شاملة لـ 128 قضية WTO رسمية</div>
  </div>

  <!-- Compare bar -->
  <div class="compare-bar" id="compare-bar" style="display:none">
    <span class="compare-info">⚡ وضع المقارنة — اختر قضيتين أو أكثر للمقارنة</span>
    <div class="compare-chips" id="compare-chips"></div>
    <button class="btn bgreen bsm" onclick="runCompare()">🔄 قارن الآن</button>
    <button class="btn bo bsm" onclick="clearCompare()">✕ إلغاء</button>
  </div>

  <div class="sbox">
    <div class="srow">
      <input class="sinput" id="sq" placeholder="ابحث... CBAM, Steel, TRIPS, SCM, DS567, Saudi..." oninput="debounce()">
      <div class="ltog">
        <button class="act" id="la" onclick="setLogic('AND')">AND</button>
        <button id="lo" onclick="setLogic('OR')">OR</button>
      </div>
      <button class="btn bp" onclick="runSearch()">🔍 بحث</button>
      <button class="btn bo" onclick="clearSearch()">مسح</button>
      <button class="btn bgreen bsm" onclick="saveSearch()">💾 حفظ</button>
    </div>
    <div class="sfilters">
      <div class="fg"><label>الاتفاقية</label>
        <select id="fag" onchange="runSearch()">
          <option value="">الكل</option>
          <option value="GATT">GATT 1994</option><option value="GATS">GATS</option>
          <option value="TRIPS">TRIPS</option><option value="SCM">SCM</option>
          <option value="ASCM">ASCM</option><option value="SPS">SPS</option>
          <option value="TBT">TBT</option><option value="ADA">Anti-Dumping</option>
          <option value="SA">Safeguards</option><option value="DSU">DSU</option>
        </select>
      </div>
      <div class="fg"><label>القطاع</label>
        <select id="fsec" onchange="runSearch()">
          <option value="">الكل</option>
          <option value="Metals">المعادن والصلب</option>
          <option value="Agriculture">الزراعة والغذاء</option>
          <option value="Anti-Dumping">مكافحة الإغراق</option>
          <option value="Subsidies">الدعم والإعانات</option>
          <option value="Safeguards">الحماية والإجراءات</option>
          <option value="Intellectual">الملكية الفكرية</option>
          <option value="Services">الخدمات</option>
          <option value="Standards">المعايير والـ TBT</option>
          <option value="Energy">الطاقة والبيئة</option>
          <option value="Textiles">المنسوجات</option>
        </select>
      </div>
      <div class="fg"><label>الدولة الشاكية</label>
        <select id="fcomp" onchange="runSearch()"><option value="">الكل</option></select>
      </div>
      <div class="fg"><label>الدولة المدعى عليها</label>
        <select id="fresp" onchange="runSearch()"><option value="">الكل</option></select>
      </div>
      <div class="fg"><label>المرحلة الإجرائية</label>
        <select id="fst" onchange="runSearch()">
          <option value="">الكل</option>
          <option value="Completed">Completed</option>
          <option value="Compliance">Compliance</option>
          <option value="Consultations">Consultations</option>
          <option value="Panel">Panel</option>
          <option value="Appeal">Appeal</option>
          <option value="Implementation">Implementation</option>
        </select>
      </div>
      <div class="fg"><label>🇸🇦 الصلة بالمملكة</label>
        <select id="fsa" onchange="runSearch()">
          <option value="">الكل</option>
          <option value="HIGH">عالية</option>
          <option value="MEDIUM">متوسطة</option>
          <option value="LOW">منخفضة</option>
        </select>
      </div>
      <div class="fg"><label>📂 مصدر البيانات</label>
        <select id="fsrc" onchange="runSearch()">
          <option value="all">الكل (128 قضية)</option>
          <option value="pdf">📄 PDF رسمي 1995-2022</option>
          <option value="curated">⭐ منتقى سعودي</option>
        </select>
      </div>
    </div>
    <div class="srci">
      <span style="color:var(--ae)">●</span>
      <span id="src-cnt">يتم التحميل...</span>
      <span>•</span>
      <span style="color:var(--t2)">المصدر: منشور WTO الرسمي 1995-2022 + قضايا سعودية منتقاة</span>
    </div>
  </div>

  <div class="rh">
    <div class="rcnt">عُثر على <strong id="rcnt">—</strong> قضية</div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <button class="btn bo bsm" onclick="toggleCompareMode()" id="compare-toggle">⚡ وضع المقارنة</button>
      <span style="font-size:11px;color:var(--t2)">ترتيب:</span>
      <select id="sort-by" onchange="runSearch()" style="background:#0d1e35;border:1px solid var(--b0);border-radius:7px;color:#e8f0fe;font-family:var(--font-ar);font-size:11px;padding:5px 9px;outline:none">
        <option value="relevance">صلة بالمملكة</option>
        <option value="year">السنة</option>
        <option value="ds">رقم DS</option>
      </select>
    </div>
  </div>

  <div class="dgrid" id="dgrid">
    <div class="empty" style="grid-column:1/-1"><div class="spin"></div><p style="margin-top:10px;font-size:12px">جارٍ تحميل 128 قضية رسمية...</p></div>
  </div>
  <div id="pgn"></div>
</div>

<!-- ══ DASHBOARD ══ -->
<div class="sec" id="sec-dash">
  <div class="section-h">📊 لوحة التحكم التحليلية — WTO Dispute Statistics</div>
  <div class="sgrid4">
    <div class="sc"><div class="sv" id="st-total">—</div><div class="sl">إجمالي القضايا</div></div>
    <div class="sc"><div class="sv" id="st-direct">—</div><div class="sl">قضايا مباشرة للمملكة</div></div>
    <div class="sc"><div class="sv" id="st-third">—</div><div class="sl">المملكة كطرف ثالث</div></div>
    <div class="sc"><div class="sv" id="st-high">—</div><div class="sl">صلة عالية بالمصالح</div></div>
  </div>
  <div class="cgrid2">
    <div class="cc"><div class="ctit">⚖️ الاتفاقيات الأكثر استناداً</div><div id="ch-ag"></div></div>
    <div class="cc"><div class="ctit">🏭 القطاعات الأكثر تكراراً</div><div id="ch-sec"></div></div>
  </div>
  <div class="cgrid2">
    <div class="cc"><div class="ctit">📅 القضايا حسب السنة</div><div id="ch-yr"></div></div>
    <div class="cc"><div class="ctit">🔄 المرحلة الإجرائية</div><div id="ch-st"></div></div>
  </div>
  <div class="cgrid2">
    <div class="cc"><div class="ctit">⚔️ أكثر الدول شكوى</div><div id="ch-comp"></div></div>
    <div class="cc"><div class="ctit">🛡️ أكثر الدول مدعى عليها</div><div id="ch-resp"></div></div>
  </div>
</div>

<!-- ══ SAUDI WATCH ══ -->
<div class="sec" id="sec-saudi">
  <div class="shero">
    <div class="sflag"><div class="fs fsG"></div><div class="fs fsAu"></div><div class="fs fsG"></div></div>
    <div class="sh2">🇸🇦 Saudi WTO Disputes Watch</div>
    <div class="shp">رصد وتحليل القضايا ذات الأثر على مصالح المملكة ودول مجلس التعاون الخليجي</div>
  </div>
  <!-- Sector filter cards -->
  <div class="sector-cards" id="sector-cards"></div>
  <div class="dgrid" id="saudi-dgrid">
    <div class="empty" style="grid-column:1/-1"><div class="spin"></div></div>
  </div>
</div>

<!-- ══ MCP TOOLS ══ -->
<div class="sec" id="sec-mcp">
  <div class="mcp-hero">
    <div class="mcp-title">⚡ WTO Dispute Settlement MCP Server <span class="mcp-badge">READ-ONLY v1.0</span></div>
    <div class="mcp-sub">نظام MCP متخصص في استعلام وتحليل بيانات قضايا تسوية المنازعات في WTO — يتصل بالمصادر الرسمية بطريقة منظمة وآمنة وقابلة للتوسع</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:.8rem">
      <span style="font-size:11px;color:var(--t2)">المصادر:</span>
      <span style="font-size:11px;color:var(--ae)">WTO Official DB</span>
      <span style="color:var(--t2)">•</span>
      <span style="font-size:11px;color:var(--ae)">DSU Framework</span>
      <span style="color:var(--t2)">•</span>
      <span style="font-size:11px;color:var(--ae)">AI Analysis Layer</span>
    </div>
  </div>
  <div class="tools-grid" id="tools-grid"></div>
</div>

<!-- ══ AI CHAT ══ -->
<div class="sec" id="sec-chat">
  <div class="section-h">🤖 المساعد القانوني الذكي — WTO Legal AI</div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
    <button class="btn bo bsm" onclick="preset('ما هي قضايا CBAM وتأثيرها على الصادرات السعودية؟')">CBAM والمملكة</button>
    <button class="btn bo bsm" onclick="preset('اشرح اتفاقية SCM وأثرها على الدعم الصناعي')">SCM Agreement</button>
    <button class="btn bo bsm" onclick="preset('ما موقف المملكة في قضية DS567؟')">DS567 المملكة</button>
    <button class="btn bo bsm" onclick="preset('ما هي إجراءات تسوية المنازعات في DSU؟')">إجراءات DSU</button>
    <button class="btn bo bsm" onclick="preset('What are the latest WTO anti-dumping cases affecting Saudi steel exports?')">Saudi Steel Cases</button>
  </div>
  <div class="chat-wrap">
    <div class="chat-hdr">
      <div class="av">⚖️</div>
      <div>
        <div style="font-size:13px;font-weight:700;color:var(--t0)">WTO Legal Intelligence + MCP</div>
        <div style="font-size:11px;color:var(--ae)">● متصل — مدعوم بـ MCP Server + 128 قضية رسمية</div>
      </div>
      <div style="margin-right:auto;display:flex;gap:5px">
        <button class="btn bo bsm" onclick="setLang('ar')" id="l-ar" style="border-color:rgba(201,168,76,.4);color:var(--ag)">🇸🇦 AR</button>
        <button class="btn bo bsm" onclick="setLang('en')" id="l-en">🇺🇸 EN</button>
      </div>
    </div>
    <div class="chat-msgs" id="chat-msgs">
      <div class="msg a">مرحباً! أنا مستشارك القانوني الذكي في نزاعات WTO — مدعوم بـ MCP Server وقاعدة بيانات 128 قضية رسمية.

يمكنني مساعدتك في:
• تحليل القضايا وفق GATT / GATS / TRIPS / SCM / TBT / SPS / ADA
• تقييم تأثير النزاعات على المصالح السعودية وقطاعات رؤية 2030
• شرح CBAM وتداعياته على صادرات المملكة للسوق الأوروبية  
• تحليل سوابق WTO واستخراج المواد القانونية
• إعداد مذكرات قانونية للجهات الحكومية والقطاع الخاص

كيف أساعدك؟</div>
    </div>
    <div class="chat-inp">
      <textarea class="cinp" id="cinp" rows="2" placeholder="اسأل عن أي قضية WTO، اتفاقية، أو تأثير على المملكة..." onkeydown="chatKey(event)"></textarea>
      <button class="btn bp" onclick="sendChat()">إرسال ↵</button>
    </div>
  </div>
</div>

<!-- ══ WATCHLIST ══ -->
<div class="sec" id="sec-wlist">
  <div class="section-h">🔔 القوائم المحفوظة والتنبيهات</div>
  <div style="display:flex;gap:10px;margin-bottom:1.5rem;flex-wrap:wrap">
    <div style="flex:1;min-width:240px">
      <input class="sinput" id="wname" placeholder="اسم القائمة أو التنبيه..." style="width:100%;margin-bottom:6px">
      <input class="sinput" id="wemail" placeholder="بريد إلكتروني للتنبيه (اختياري)..." style="width:100%">
    </div>
    <div style="flex:1;min-width:180px">
      <div style="font-size:11px;color:var(--t2);margin-bottom:4px">الفلاتر المحفوظة:</div>
      <div id="cur-filters" style="font-size:11px;color:var(--ab);background:rgba(0,162,255,.05);border:1px solid var(--b0);border-radius:7px;padding:6px 10px;min-height:36px"></div>
    </div>
    <button class="btn bg" onclick="addWatch()">💾 حفظ القائمة</button>
  </div>
  <div class="wlist-grid" id="wlist-grid">
    <div class="empty" style="grid-column:1/-1"><div class="ico">🔔</div><h3>لا توجد قوائم محفوظة بعد</h3><p>ابحث عن قضايا واحفظ فلاترك للمتابعة</p></div>
  </div>
</div>

<!-- ══ SOURCES ══ -->
<div class="sec" id="sec-src">
  <div class="section-h">📚 المصادر الرسمية وأدوات البحث القانوني</div>
  <div class="stitle">🌐 WTO — المصادر الرسمية</div>
  <div class="srcgrid" id="src-wto"></div>
  <div class="stitle">📡 منصات الرصد والتنبيهات</div>
  <div class="srcgrid" id="src-mon"></div>
  <div class="stitle">🇸🇦 الجهات السعودية الرسمية</div>
  <div class="srcgrid" id="src-sa"></div>
</div>

</main>

<!-- MODAL -->
<div class="mov" id="mov" onclick="closeMBg(event)">
  <div class="modal">
    <div class="mhdr">
      <div>
        <div class="mds" id="m-ds"></div>
        <div class="mtitle" id="m-title"></div>
      </div>
      <button class="mclose" onclick="closeM()">✕</button>
    </div>
    <div class="mbody">
      <div class="mtabs">
        <button class="mtab act" onclick="showTab('info')">📋 المعلومات</button>
        <button class="mtab" onclick="showTab('sum')">📝 الملخص</button>
        <button class="mtab" onclick="showTab('tl')">📅 الجدول الزمني</button>
        <button class="mtab" onclick="showTab('ai')">🤖 التحليل الذكي</button>
        <button class="mtab" onclick="showTab('risk')">⚠️ تحليل المخاطر</button>
        <button class="mtab" onclick="showTab('memo')">📄 مذكرة تنفيذية</button>
        <button class="mtab" onclick="showTab('sim')">🔗 قضايا مشابهة</button>
        <button class="mtab" onclick="showTab('docs')">🔗 الوثائق</button>
      </div>

      <!-- INFO -->
      <div class="tc act" id="tc-info">
        <div class="igrid2" id="m-igrid"></div>
        <div class="impbox"><div class="imptitle">🇸🇦 تحليل الأثر على المملكة العربية السعودية</div><div class="impval" id="m-impact"></div></div>
        <div style="margin-bottom:10px">
          <div style="font-size:10px;color:var(--t2);margin-bottom:5px;text-transform:uppercase;letter-spacing:.4px">الاتفاقيات والمواد القانونية</div>
          <div id="m-ags" style="display:flex;gap:5px;flex-wrap:wrap"></div>
        </div>
        <div style="margin-bottom:14px">
          <div style="font-size:10px;color:var(--t2);margin-bottom:5px;text-transform:uppercase;letter-spacing:.4px">الأطراف الثالثة</div>
          <div id="m-tp" style="display:flex;gap:5px;flex-wrap:wrap"></div>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <a id="m-wtolink" href="#" target="_blank" class="btn bo bsm">🔗 صفحة WTO</a>
          <button class="btn bg bsm" onclick="showTab('ai');genAI()">🤖 تحليل AI</button>
          <button class="btn bo bsm" onclick="showTab('memo');genMemo()">📄 مذكرة</button>
          <button class="btn bpurple bsm" onclick="showTab('sim');findSim()">🔗 مشابهة</button>
          <button class="btn bgreen bsm" onclick="addToCompare()">⚡ أضف للمقارنة</button>
        </div>
      </div>

      <!-- SUMMARY -->
      <div class="tc" id="tc-sum">
        <div style="margin-bottom:1rem">
          <div style="font-size:11px;color:var(--t2);margin-bottom:6px;font-weight:600">الملخص بالعربية</div>
          <div style="background:rgba(0,162,255,.04);border:1px solid rgba(0,162,255,.15);border-radius:var(--r);padding:12px;font-size:13px;line-height:1.8;color:var(--t1)" id="m-ar">—</div>
        </div>
        <div>
          <div style="font-size:11px;color:var(--t2);margin-bottom:6px;font-weight:600">English Summary</div>
          <div style="background:rgba(0,162,255,.04);border:1px solid rgba(0,162,255,.15);border-radius:var(--r);padding:12px;font-size:13px;line-height:1.8;color:var(--t1);direction:ltr;text-align:left" id="m-en">—</div>
        </div>
      </div>

      <!-- TIMELINE -->
      <div class="tc" id="tc-tl">
        <div class="timeline" id="m-tl"><div class="spin"></div></div>
      </div>

      <!-- AI -->
      <div class="tc" id="tc-ai">
        <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">
          <button class="btn bg bsm" onclick="genAI('ar')">🤖 تحليل عربي</button>
          <button class="btn bo bsm" onclick="genAI('en')">🤖 English Analysis</button>
        </div>
        <div class="aipanel" id="ai-panel">اضغط "تحليل" للحصول على تحليل قانوني متكامل بالذكاء الاصطناعي...</div>
      </div>

      <!-- RISK -->
      <div class="tc" id="tc-risk">
        <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">
          <button class="btn bg bsm" onclick="genRisk('ar')">⚠️ تحليل المخاطر — عربي</button>
          <button class="btn bo bsm" onclick="genRisk('en')">⚠️ Risk Analysis</button>
        </div>
        <div class="aipanel" id="risk-panel">اضغط لاستخراج المخاطر القانونية والتجارية...</div>
      </div>

      <!-- MEMO -->
      <div class="tc" id="tc-memo">
        <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">
          <button class="btn bg bsm" onclick="genMemo('ar','government')">🏛️ مذكرة حكومية — AR</button>
          <button class="btn bo bsm" onclick="genMemo('en','private')">💼 Private Sector EN</button>
          <button class="btn bgreen bsm" onclick="copyPanel('memo-panel')">📋 نسخ</button>
        </div>
        <div class="aipanel" id="memo-panel">اضغط لإعداد مذكرة قانونية تنفيذية مخصصة...</div>
      </div>

      <!-- SIMILAR -->
      <div class="tc" id="tc-sim">
        <div id="sim-list"><div class="spin"></div></div>
      </div>

      <!-- DOCS -->
      <div class="tc" id="tc-docs">
        <div id="docs-list"><div class="spin"></div></div>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ═══════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════
let logic='AND', chatLang='ar', chatH=[], cur=null, dbt=null;
let compareModeOn=false, compareList=[], curPage=1, PER_PAGE=24;
let watchlists=JSON.parse(localStorage.getItem('wto_watchlists')||'[]');

// ═══════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════
function showSec(n){
  document.querySelectorAll('.sec').forEach(s=>s.classList.remove('act'));
  document.querySelectorAll('.nb').forEach(b=>b.classList.remove('act'));
  document.getElementById('sec-'+n).classList.add('act');
  document.getElementById('nb-'+n).classList.add('act');
  if(n==='dash')loadDash();
  if(n==='saudi')loadSaudi();
  if(n==='src')loadSrc();
  if(n==='mcp')loadMCP();
  if(n==='wlist')loadWList();
}

// ═══════════════════════════════════════════════════════════
// SEARCH
// ═══════════════════════════════════════════════════════════
function g(id){const e=document.getElementById(id);return e?e.value:'';}
function setLogic(l){logic=l;document.getElementById('la').classList.toggle('act',l==='AND');document.getElementById('lo').classList.toggle('act',l==='OR');runSearch();}
function debounce(){clearTimeout(dbt);dbt=setTimeout(runSearch,380);}

function clearSearch(){
  ['sq','fag','fsec','fcomp','fresp','fst','fsa','fsrc'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  runSearch();
}

async function runSearch(page=1){
  curPage=page;
  const grid=document.getElementById('dgrid');
  grid.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="spin"></div></div>';
  const params=new URLSearchParams({q:g('sq'),year:'',agreement:g('fag'),sector:g('fsec'),complainant:g('fcomp'),respondent:g('fresp'),status:g('fst'),saudi_relevance:g('fsa'),logic,source:g('fsrc'),page,per_page:PER_PAGE});
  try{
    const r=await fetch('/api/disputes?'+params);
    if(!r.ok)throw new Error('HTTP '+r.status);
    const txt=await r.text();
    let data;
    try{data=JSON.parse(txt);}catch(e){console.error('Non-JSON:',txt.substring(0,200));throw e;}
    document.getElementById('rcnt').textContent=data.total;
    if(data.source_counts){
      document.getElementById('src-cnt').textContent=`الكل: ${data.source_counts.all} | PDF رسمي: ${data.source_counts.pdf} | منتقى: ${data.source_counts.curated}`;
    }
    renderCards(data.disputes,'dgrid');
    renderPgn(data.total,data.page,data.pages,'pgn',runSearch);
  }catch(e){
    grid.innerHTML=`<div class="empty" style="grid-column:1/-1"><div class="ico">⚠️</div><h3>خطأ في الاتصال</h3><p>${e.message}</p><button class="btn bo" style="margin-top:10px" onclick="runSearch()">🔄 إعادة المحاولة</button></div>`;
  }
}

function stageClass(s){
  if(!s)return 'sCl';
  s=s.toLowerCase();
  if(s.includes('consult'))return 'sCo';
  if(s.includes('panel'))return 'sPa';
  if(s.includes('appeal'))return 'sAp';
  if(s.includes('implement'))return 'sIm';
  if(s.includes('compli'))return 'sCom';
  return 'sCl';
}

function renderCards(arr,id){
  const g=document.getElementById(id);
  if(!arr||!arr.length){g.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="ico">🔍</div><h3>لا توجد نتائج</h3><p>جرب تغيير معايير البحث</p></div>';return;}
  const srt=g('sort-by')||'relevance';
  const sorted=[...arr].sort((a,b)=>{
    if(srt==='year')return (b.year||0)-(a.year||0);
    if(srt==='ds')return a.ds_number.localeCompare(b.ds_number);
    const o={HIGH:0,MEDIUM:1,LOW:2};
    return (o[a.saudi_relevance]??3)-(o[b.saudi_relevance]??3);
  });
  const isPdf=d=>d.source&&d.source.includes('1995-2022');
  g.innerHTML=sorted.map(d=>{
    const stage=d.stage||d.status||'N/A';
    const sc=stageClass(stage);
    const sel=compareList.includes(d.ds_number);
    return `<div class="dc ${d.saudi_relevance==='HIGH'?'sh':''} ${sel?'selected':''}" onclick="openModal('${d.ds_number}')">
      <div class="ch">
        <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
          <span class="dsbdg">${d.ds_number}</span>
          <span class="${isPdf(d)?'src-pip src-pdf':'src-pip src-cu'}">${isPdf(d)?'📄 PDF':'⭐'}</span>
        </div>
        <span class="rbdg r${d.saudi_relevance||'L'}">🇸🇦 ${d.saudi_relevance||'LOW'}</span>
      </div>
      <div class="ctitle">${d.title}</div>
      <div class="cparties">
        <span class="ptag c">⚔️ ${(d.complainant||'').substring(0,28)}</span>
        <span class="ptag r">🛡️ ${(d.respondent||'').substring(0,28)}</span>
      </div>
      <div class="cags">${(d.agreements||[]).slice(0,3).map(a=>`<span class="achip">${a.substring(0,22)}</span>`).join('')}</div>
      <div class="cft">
        <span class="sbdg ${sc}">${stage}</span>
        <span class="cyr">${d.year||'—'}</span>
      </div>
      ${compareModeOn?`<div class="chk-sel" onclick="event.stopPropagation();toggleCompare('${d.ds_number}')">
        <input type="checkbox" ${sel?'checked':''} style="cursor:pointer"> إضافة للمقارنة
      </div>`:''}
    </div>`;
  }).join('');
}

function renderPgn(total,cur,pages,id,fn){
  const el=document.getElementById(id);
  if(!el||pages<=1){if(el)el.innerHTML='';return;}
  let h='<div class="pgn">';
  if(cur>1)h+=`<button class="btn bo bsm" onclick="${fn.name}(${cur-1})">→ السابق</button>`;
  const s=Math.max(1,cur-2),e=Math.min(pages,cur+2);
  if(s>1)h+=`<button class="btn bo bsm" onclick="${fn.name}(1)">1</button><span style="color:var(--t2)">…</span>`;
  for(let i=s;i<=e;i++)h+=`<button class="btn ${i===cur?'bp':'bo'} bsm" style="min-width:32px" onclick="${fn.name}(${i})">${i}</button>`;
  if(e<pages)h+=`<span style="color:var(--t2)">…</span><button class="btn bo bsm" onclick="${fn.name}(${pages})">${pages}</button>`;
  if(cur<pages)h+=`<button class="btn bo bsm" onclick="${fn.name}(${cur+1})">← التالي</button>`;
  h+=`<span style="font-size:11px;color:var(--t2)">صفحة ${cur}/${pages} (${total} قضية)</span></div>`;
  el.innerHTML=h;
}

// Load parties dropdown
async function loadParties(){
  try{
    const r=await fetch('/api/parties');
    const d=await r.json();
    const cs=document.getElementById('fcomp'),rs=document.getElementById('fresp');
    if(cs)d.complainants.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;cs.appendChild(o);});
    if(rs)d.respondents.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;rs.appendChild(o);});
  }catch(e){console.error('parties error',e);}
}

// ═══════════════════════════════════════════════════════════
// COMPARE
// ═══════════════════════════════════════════════════════════
function toggleCompareMode(){
  compareModeOn=!compareModeOn;
  document.getElementById('compare-toggle').textContent=compareModeOn?'✕ إلغاء المقارنة':'⚡ وضع المقارنة';
  document.getElementById('compare-toggle').className=compareModeOn?'btn bgreen bsm':'btn bo bsm';
  if(!compareModeOn){clearCompare();return;}
  toast('⚡ وضع المقارنة — اختر قضيتين أو أكثر');
  runSearch();
}

function toggleCompare(ds){
  const i=compareList.indexOf(ds);
  if(i>=0)compareList.splice(i,1);
  else if(compareList.length<4)compareList.push(ds);
  else{toast('⚠️ الحد الأقصى 4 قضايا للمقارنة');return;}
  updateCompareBar();
  runSearch();
}

function addToCompare(){
  if(!cur)return;
  toggleCompare(cur.ds_number);
  closeM();
}

function updateCompareBar(){
  const bar=document.getElementById('compare-bar');
  const chips=document.getElementById('compare-chips');
  if(compareList.length>0){
    bar.style.display='flex';
    chips.innerHTML=compareList.map(ds=>`<span class="cchip">${ds} <span class="cchip-x" onclick="toggleCompare('${ds}')">✕</span></span>`).join('');
  }else{bar.style.display='none';}
}

async function runCompare(){
  if(compareList.length<2){toast('⚠️ اختر قضيتين على الأقل');return;}
  const r=await fetch('/api/ai/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_numbers:compareList,language:chatLang})});
  const d=await r.json();
  if(d.error){toast('❌ '+d.error);return;}
  showCompareModal(d.comparison);
}

function showCompareModal(text){
  document.getElementById('m-ds').textContent='مقارنة: '+compareList.join(' vs ');
  document.getElementById('m-title').textContent='تحليل مقارن — '+compareList.join(', ');
  document.getElementById('ai-panel').textContent=text;
  showTab('ai');
  document.getElementById('mov').classList.add('open');
}

function clearCompare(){compareList=[];compareModeOn=false;document.getElementById('compare-bar').style.display='none';document.getElementById('compare-toggle').textContent='⚡ وضع المقارنة';document.getElementById('compare-toggle').className='btn bo bsm';runSearch();}

// ═══════════════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════════════
async function openModal(ds){
  try{
    const r=await fetch('/api/disputes/'+ds);
    cur=await r.json();
    if(cur.error)return;
    document.getElementById('m-ds').textContent=cur.ds_number;
    document.getElementById('m-title').textContent=cur.title;
    const stage=cur.stage||cur.status||'N/A';
    document.getElementById('m-igrid').innerHTML=`
      <div class="ii"><div class="ilbl">الدولة الشاكية</div><div class="ival">⚔️ ${cur.complainant||'—'}</div></div>
      <div class="ii"><div class="ilbl">الدولة المدعى عليها</div><div class="ival">🛡️ ${cur.respondent||'—'}</div></div>
      <div class="ii"><div class="ilbl">المرحلة الإجرائية</div><div class="ival"><span class="sbdg ${stageClass(stage)}">${stage}</span></div></div>
      <div class="ii"><div class="ilbl">السنة</div><div class="ival">${cur.year||'—'}</div></div>
      <div class="ii"><div class="ilbl">القطاع</div><div class="ival">${cur.sector||'—'}</div></div>
      <div class="ii"><div class="ilbl">الصلة بالمملكة</div><div class="ival"><span class="rbdg r${cur.saudi_relevance||'L'}">${cur.saudi_relevance||'LOW'}</span></div></div>`;
    document.getElementById('m-impact').textContent=cur.saudi_impact||'—';
    document.getElementById('m-ags').innerHTML=(cur.agreements||[]).map(a=>`<span class="achip">${a}</span>`).join('');
    const tps=cur.third_parties||[];
    document.getElementById('m-tp').innerHTML=tps.length?tps.map(p=>`<span style="padding:2px 8px;border-radius:6px;font-size:11px;background:rgba(255,255,255,.04);border:1px solid var(--b0);color:var(--t1)">${p}</span>`).join(''):`<span style="font-size:11px;color:var(--t2)">لا توجد أطراف ثالثة في قاعدة البيانات الحالية</span>`;
    document.getElementById('m-wtolink').href=`https://www.wto.org/english/tratop_e/dispu_e/cases_e/${cur.ds_number.toLowerCase()}_e.htm`;
    const arEl=document.getElementById('m-ar');
    const enEl=document.getElementById('m-en');
    if(arEl){arEl.textContent=cur.summary_ar&&cur.summary_ar.trim()?cur.summary_ar:'[الملخص العربي غير متوفر — استخدم تحليل AI لتوليده تلقائياً]';}
    if(enEl){enEl.textContent=cur.summary_en||'—';}
    // Reset panels
    document.getElementById('ai-panel').textContent='اضغط "تحليل" للحصول على تحليل قانوني بالذكاء الاصطناعي...';
    document.getElementById('risk-panel').textContent='اضغط لاستخراج المخاطر القانونية والتجارية...';
    document.getElementById('memo-panel').textContent='اضغط لإعداد مذكرة قانونية تنفيذية...';
    document.getElementById('m-tl').innerHTML='<div class="spin"></div>';
    document.getElementById('sim-list').innerHTML='<div class="spin"></div>';
    document.getElementById('docs-list').innerHTML='<div class="spin"></div>';
    showTab('info');
    document.getElementById('mov').classList.add('open');
    // Auto-load timeline
    loadTimeline();
  }catch(e){console.error(e);}
}

function closeM(){document.getElementById('mov').classList.remove('open');cur=null;}
function closeMBg(e){if(e.target===document.getElementById('mov'))closeM();}
function showTab(t){
  document.querySelectorAll('.tc').forEach(x=>x.classList.remove('act'));
  document.querySelectorAll('.mtab').forEach(x=>x.classList.remove('act'));
  document.getElementById('tc-'+t).classList.add('act');
  const map={info:0,sum:1,tl:2,ai:3,risk:4,memo:5,sim:6,docs:7};
  const tabs=document.querySelectorAll('.mtab');
  if(tabs[map[t]])tabs[map[t]].classList.add('act');
}

// ═══════════════════════════════════════════════════════════
// TIMELINE
// ═══════════════════════════════════════════════════════════
async function loadTimeline(){
  if(!cur)return;
  try{
    const r=await fetch('/api/mcp/get_case_timeline',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_number:cur.ds_number})});
    const d=await r.json();
    const el=document.getElementById('m-tl');
    if(d.error){el.innerHTML=`<p style="color:var(--ar);font-size:12px">${d.error}</p>`;return;}
    el.innerHTML=d.timeline.map((t,i)=>`
      <div class="tl-item">
        <div class="tl-dot ${t.status==='current'?'cur':''}">${t.step}</div>
        <div class="tl-content">
          <div class="tl-event">${t.event}</div>
          <div class="tl-year">${t.year}</div>
          ${t.wto_articles?`<div class="tl-art">${t.wto_articles}</div>`:''}
        </div>
      </div>`).join('');
  }catch(e){document.getElementById('m-tl').innerHTML='<p style="font-size:12px;color:var(--t2)">خطأ في تحميل الجدول الزمني</p>';}
}

// ═══════════════════════════════════════════════════════════
// AI FUNCTIONS
// ═══════════════════════════════════════════════════════════
async function genAI(lang='ar'){
  if(!cur)return;
  const p=document.getElementById('ai-panel');
  p.innerHTML='<div style="display:flex;align-items:center;gap:10px;padding:10px;color:var(--ab)"><div class="spin"></div>جارٍ التحليل بالذكاء الاصطناعي...</div>';
  try{
    const r=await fetch('/api/ai/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_number:cur.ds_number,language:lang})});
    const d=await r.json();
    p.textContent=d.error?'⚠️ '+d.error:d.analysis;
  }catch(e){p.textContent='⚠️ خطأ في الاتصال — تحقق من ANTHROPIC_API_KEY';}
}

async function genRisk(lang='ar'){
  if(!cur)return;
  const p=document.getElementById('risk-panel');
  p.innerHTML='<div style="display:flex;align-items:center;gap:10px;padding:10px;color:var(--ao)"><div class="spin"></div>جارٍ تحليل المخاطر...</div>';
  try{
    const r=await fetch('/api/ai/risk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_number:cur.ds_number,language:lang})});
    const d=await r.json();
    p.textContent=d.error?'⚠️ '+d.error:d.risk_analysis;
  }catch(e){p.textContent='⚠️ خطأ في الاتصال';}
}

async function genMemo(lang='ar',audience='government'){
  if(!cur)return;
  const p=document.getElementById('memo-panel');
  p.innerHTML='<div style="display:flex;align-items:center;gap:10px;padding:10px;color:var(--ag)"><div class="spin"></div>جارٍ إعداد المذكرة القانونية...</div>';
  try{
    const r=await fetch('/api/ai/memo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_number:cur.ds_number,language:lang,audience})});
    const d=await r.json();
    p.textContent=d.error?'⚠️ '+d.error:d.memo;
  }catch(e){p.textContent='⚠️ خطأ في الاتصال';}
}

async function findSim(){
  if(!cur)return;
  const el=document.getElementById('sim-list');
  el.innerHTML='<div class="spin"></div>';
  try{
    const r=await fetch('/api/mcp/find_similar_disputes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ds_number:cur.ds_number,limit:6})});
    const d=await r.json();
    if(d.error){el.innerHTML=`<p style="color:var(--ar)">${d.error}</p>`;return;}
    el.innerHTML=(d.similar_cases||[]).map(s=>`
      <div style="background:rgba(255,255,255,.03);border:1px solid var(--b0);border-radius:var(--r);padding:10px;margin-bottom:8px;cursor:pointer" onclick="closeM();setTimeout(()=>openModal('${s.ds_number}'),100)">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span class="dsbdg">${s.ds_number}</span>
          <span style="font-size:10px;color:var(--ae);font-family:var(--font-mo)">تشابه: ${s.similarity_score}</span>
        </div>
        <div style="font-size:12px;color:var(--t0);margin-bottom:4px">${s.title}</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">${(s.shared_agreements||[]).map(a=>`<span class="achip">${a}</span>`).join('')}</div>
      </div>`).join('')||'<p style="font-size:12px;color:var(--t2)">لا توجد قضايا مشابهة في قاعدة البيانات الحالية</p>';
  }catch(e){el.innerHTML='<p style="font-size:12px;color:var(--ar)">خطأ في التحميل</p>';}
}

async function loadDocs(){
  if(!cur)return;
  const el=document.getElementById('docs-list');
  try{
    const r=await fetch('/api/mcp/get_dispute_documents?ds_number='+cur.ds_number);
    const d=await r.json();
    el.innerHTML=`<p style="font-size:11px;color:var(--t2);margin-bottom:10px">⚠️ ${d.disclaimer||''}</p>`+
      (d.documents||[]).map(doc=>`<a href="${doc.url}" target="_blank" style="display:block;background:rgba(255,255,255,.03);border:1px solid var(--b0);border-radius:var(--r);padding:10px;margin-bottom:6px;text-decoration:none;transition:all .15s" onmouseover="this.style.borderColor='var(--b1)'" onmouseout="this.style.borderColor='var(--b0)'">
        <div style="font-size:12px;font-weight:600;color:var(--ab);margin-bottom:3px">🔗 ${doc.type}</div>
        <div style="font-size:11px;color:var(--t2)">${doc.description}</div>
      </a>`).join('');
  }catch(e){el.innerHTML='<p style="font-size:12px;color:var(--ar)">خطأ في تحميل الوثائق</p>';}
}

function copyPanel(id){navigator.clipboard&&navigator.clipboard.writeText(document.getElementById(id).textContent);toast('✅ تم النسخ');}

// ═══════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════
async function loadDash(){
  try{
    const r=await fetch('/api/stats');
    const s=await r.json();
    document.getElementById('st-total').textContent=s.total;
    document.getElementById('st-direct').textContent=s.saudi_involvement.direct;
    document.getElementById('st-third').textContent=s.saudi_involvement.third_party;
    document.getElementById('st-high').textContent=s.saudi_involvement.high;
    renderBar('ch-ag',s.by_agreement,8);
    renderBar('ch-sec',s.by_sector,8);
    renderBar('ch-yr',s.by_year,10);
    renderBar('ch-st',s.by_status,6);
    renderBar('ch-comp',s.top_complainants,7);
    renderBar('ch-resp',s.top_respondents,7);
  }catch(e){console.error(e);}
}

function renderBar(id,data,top=8){
  const el=document.getElementById(id);
  if(!el)return;
  const entries=Object.entries(data).sort((a,b)=>b[1]-a[1]).slice(0,top);
  const mx=Math.max(...entries.map(e=>e[1]),1);
  el.innerHTML=entries.map(([k,v])=>`<div class="brow"><div class="blbl">${k}</div><div class="btrk"><div class="bfll" style="width:${Math.round(v/mx*100)}%"></div></div><div class="bcnt">${v}</div></div>`).join('');
}

// ═══════════════════════════════════════════════════════════
// SAUDI WATCH
// ═══════════════════════════════════════════════════════════
const SECTORS=[
  {ico:'⚡',label:'CBAM & الكربون',q:'carbon'},
  {ico:'🛢️',label:'الطاقة والنفط',q:'energy'},
  {ico:'🏗️',label:'الصلب والمعادن',q:'metals'},
  {ico:'🧪',label:'البتروكيماويات',q:'petrochem'},
  {ico:'🌱',label:'الزراعة والغذاء',q:'agriculture'},
  {ico:'💊',label:'الملكية الفكرية',q:'trips'},
  {ico:'🌿',label:'الطاقة المتجددة',q:'renewable'},
  {ico:'🚢',label:'الدعم الصناعي',q:'subsidies'},
  {ico:'🛡️',label:'مكافحة الإغراق',q:'dumping'},
  {ico:'📋',label:'الإجراءات الوقائية',q:'safeguard'},
  {ico:'🔌',label:'الخدمات الرقمية',q:'services'},
  {ico:'🌍',label:'التجارة والبيئة',q:'environment'},
];

function loadSaudi(){
  const sc=document.getElementById('sector-cards');
  sc.innerHTML=SECTORS.map((s,i)=>`<div class="scard" id="sc-${i}" onclick="filterSaudi('${s.q}',${i})"><div class="scard-ico">${s.ico}</div><div class="scard-ttl">${s.label}</div></div>`).join('');
  fetchSaudi('');
}

function filterSaudi(q,idx){
  document.querySelectorAll('.scard').forEach(c=>c.classList.remove('active-sec'));
  const el=document.getElementById('sc-'+idx);
  if(el)el.classList.add('active-sec');
  fetchSaudi(q);
}

async function fetchSaudi(q){
  const g=document.getElementById('saudi-dgrid');
  g.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="spin"></div></div>';
  try{
    let url=q?`/api/disputes?q=${encodeURIComponent(q)}&per_page=50`:'/api/saudi-watch';
    const r=await fetch(url);
    const d=await r.json();
    renderCards(d.disputes||[],'saudi-dgrid');
  }catch(e){g.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="ico">⚠️</div><p>خطأ في التحميل</p></div>';}
}

// ═══════════════════════════════════════════════════════════
// MCP TOOLS
// ═══════════════════════════════════════════════════════════
const MCP_TOOLS=[
  {name:'search_disputes',desc:'البحث في قضايا WTO حسب الدولة، السنة، الاتفاقية، القطاع أو الموضوع',placeholder:'مثال: {"query":"steel","year":"2018","complainant":"India"}',endpoint:'/api/mcp/search_disputes'},
  {name:'get_dispute_details',desc:'الحصول على تفاصيل كاملة لقضية محددة (DSxxx)',placeholder:'مثال: {"ds_number":"DS567"}',endpoint:'/api/mcp/get_dispute_details'},
  {name:'get_dispute_documents',desc:'روابط الوثائق الرسمية المرتبطة بالقضية — Panel Reports, AB Reports, DSB Minutes',placeholder:'مثال: {"ds_number":"DS567"}',endpoint:'/api/mcp/get_dispute_documents'},
  {name:'extract_legal_claims',desc:'استخراج الاتفاقيات والمواد القانونية محل النزاع تلقائياً',placeholder:'مثال: {"ds_number":"DS2"}',endpoint:'/api/mcp/extract_legal_claims'},
  {name:'get_case_timeline',desc:'بناء خط زمني إجرائي للقضية وفق DSU Articles',placeholder:'مثال: {"ds_number":"DS567"}',endpoint:'/api/mcp/get_case_timeline'},
  {name:'find_similar_disputes',desc:'استخراج القضايا المشابهة استناداً على الاتفاقيات والقطاع والدولة',placeholder:'مثال: {"ds_number":"DS567","limit":5}',endpoint:'/api/mcp/find_similar_disputes'},
  {name:'analyze_saudi_relevance',desc:'تحليل مدى ارتباط القضية بمصالح المملكة العربية السعودية التجارية والاستراتيجية',placeholder:'مثال: {"ds_number":"DS627"}',endpoint:'/api/mcp/analyze_saudi_relevance'},
  {name:'generate_legal_summary',desc:'توليد ملخص قانوني تنفيذي بالعربية والإنجليزية (يتطلب ANTHROPIC_API_KEY)',placeholder:'مثال: {"ds_number":"DS567","language":"both"}',endpoint:'/api/mcp/generate_legal_summary'},
];

function loadMCP(){
  document.getElementById('tools-grid').innerHTML=MCP_TOOLS.map((t,i)=>`
    <div class="tool-card">
      <div class="tool-name">⚡ ${t.name}</div>
      <div class="tool-desc">${t.desc}</div>
      <input class="tool-input" id="ti-${i}" placeholder="${t.placeholder}" value='{"ds_number":"DS567"}'>
      <div style="display:flex;gap:5px;margin-bottom:6px">
        <button class="btn bgreen bsm" onclick="runTool(${i},'${t.endpoint}')">▶ تشغيل</button>
        <span style="font-size:10px;color:var(--t2);align-self:center">GET/POST</span>
      </div>
      <div class="tool-result" id="tr-${i}">النتيجة ستظهر هنا...</div>
    </div>`).join('');
}

async function runTool(idx,endpoint){
  const inp=document.getElementById('ti-'+idx);
  const res=document.getElementById('tr-'+idx);
  res.textContent='⏳ جارٍ التشغيل...';
  try{
    let body={};
    try{body=JSON.parse(inp.value||'{}');}catch(e){body={ds_number:inp.value};}
    const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();
    res.textContent=JSON.stringify(d,null,2);
  }catch(e){res.textContent='❌ خطأ: '+e.message;}
}

// ═══════════════════════════════════════════════════════════
// WATCHLIST
// ═══════════════════════════════════════════════════════════
function saveSearch(){
  const name=g('wname')||'بحث محفوظ '+new Date().toLocaleDateString('ar-SA');
  const filters={q:g('sq'),agreement:g('fag'),sector:g('fsec'),complainant:g('fcomp'),respondent:g('fresp'),status:g('fst'),saudi:g('fsa')};
  const item={id:Date.now(),name,filters,email:g('wemail'),created:new Date().toISOString()};
  watchlists.unshift(item);
  localStorage.setItem('wto_watchlists',JSON.stringify(watchlists));
  toast('✅ تم حفظ البحث: '+name);
}

function addWatch(){saveSearch();showSec('wlist');}

function loadWList(){
  // Update current filters display
  const cf=document.getElementById('cur-filters');
  const filters=[g('sq'),g('fag'),g('fsec'),g('fcomp'),g('fresp')].filter(Boolean);
  if(cf)cf.textContent=filters.length?filters.join(' + '):'لا توجد فلاتر نشطة';
  // Render list
  const wg=document.getElementById('wlist-grid');
  if(!watchlists.length){wg.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="ico">🔔</div><h3>لا توجد قوائم محفوظة</h3><p>ابحث وادفع "حفظ" لإضافة قائمة</p></div>';return;}
  wg.innerHTML=watchlists.map(w=>`<div class="witem">
    <button class="witem-del" onclick="delWatch(${w.id})">🗑️</button>
    <div class="witem-title">🔔 ${w.name}</div>
    <div class="witem-tags">${Object.entries(w.filters).filter(([,v])=>v).map(([k,v])=>`<span class="wtag">${k}: ${v}</span>`).join('')||'<span class="wtag">كل القضايا</span>'}</div>
    ${w.email?`<div style="font-size:10px;color:var(--t2)">📧 ${w.email}</div>`:''}
    <div style="margin-top:8px"><button class="btn bo bsm" onclick="applyWatch(${w.id})">🔍 تطبيق البحث</button></div>
  </div>`).join('');
}

function delWatch(id){watchlists=watchlists.filter(w=>w.id!==id);localStorage.setItem('wto_watchlists',JSON.stringify(watchlists));loadWList();}
function applyWatch(id){
  const w=watchlists.find(x=>x.id===id);
  if(!w)return;
  const f=w.filters;
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.value=v||'';};
  set('sq',f.q);set('fag',f.agreement);set('fsec',f.sector);set('fcomp',f.complainant);set('fresp',f.respondent);set('fst',f.status);set('fsa',f.saudi);
  showSec('search');runSearch();
}

// ═══════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════
function setLang(l){chatLang=l;document.getElementById('l-ar').style.borderColor=l==='ar'?'rgba(201,168,76,.5)':'';document.getElementById('l-en').style.borderColor=l==='en'?'rgba(0,162,255,.5)':'';}
function preset(t){document.getElementById('cinp').value=t;showSec('chat');sendChat();}
function chatKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat();}}

async function sendChat(){
  const inp=document.getElementById('cinp');
  const txt=inp.value.trim();
  if(!txt)return;
  inp.value='';
  addMsg('u',txt);
  chatH.push({role:'user',content:txt});
  const lid=addMsg('a','<div style="display:flex;align-items:center;gap:8px;color:var(--ab)"><div class="spin"></div>يُحلل...</div>',true);
  try{
    const r=await fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:chatH,language:chatLang})});
    const d=await r.json();
    const reply=d.response||d.error||'حدث خطأ';
    updateMsg(lid,reply);
    chatH.push({role:'assistant',content:reply});
  }catch(e){updateMsg(lid,'⚠️ خطأ في الاتصال — تحقق من ANTHROPIC_API_KEY في Render Environment');}
}

let msgId=0;
function addMsg(role,html,isHtml=false){
  const id='msg-'+(++msgId);
  const msgs=document.getElementById('chat-msgs');
  const d=document.createElement('div');
  d.className='msg '+role;d.id=id;
  if(isHtml)d.innerHTML=html;else d.textContent=html;
  msgs.appendChild(d);msgs.scrollTop=99999;
  return id;
}
function updateMsg(id,txt){const el=document.getElementById(id);if(el){el.textContent=txt;el.closest('.chat-msgs').scrollTop=99999;}}

// ═══════════════════════════════════════════════════════════
// SOURCES
// ═══════════════════════════════════════════════════════════
async function loadSrc(){
  try{
    const r=await fetch('/api/sources');
    const d=await r.json();
    renderSrc('src-wto',d.wto_official);
    renderSrc('src-mon',d.monitoring);
    renderSrc('src-sa',d.saudi_official);
  }catch(e){}
}
function renderSrc(id,items){
  const el=document.getElementById(id);
  if(!el||!items)return;
  el.innerHTML=items.map(s=>`<a class="srcc" href="${s.url}" target="_blank" rel="noopener"><div class="srcnm">🔗 ${s.name}</div><div class="srcd">${s.description||''}</div><div class="srcu">💡 ${s.use_case||''}</div></a>`).join('');
}

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000);}

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded',()=>{
  loadParties();
  runSearch();
});

// Docs tab auto-load
document.addEventListener('click',e=>{
  if(e.target.classList.contains('mtab')&&e.target.textContent.includes('الوثائق')){
    setTimeout(loadDocs,100);
  }
});
</script>
</body>
</html>
"""
