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
WTO_PDF_DISPUTES = [{"ds_number": "DS2", "title": "US – GASOLINE", "complainant": "Brazil, Venezuela", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. III and XX"], "articles": [], "subject": "The “Gasoline Rule” under the US Clean Air Act that set out the rules for establishing baseline figures for gasoline sold on the US market (different methods for domestic and imported gasoline), with ", "sector": "Energy & Environment", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Energy & Environment السعودي", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure treated imported gasoline “less favourably” than domestic gasoline in violation of Art. III:4, as imported gasoline effectively experienced less favourable sales conditions than those afforded to domestic gasoline. In particular, under the regulation, importers had to adapt to an average standard, i.e. “statutory baseline”, that had no connection to the particular gasoline imported, while refiners of domestic gasoline had only to meet a standard linked to their own product in 1990, i.e. individual refinery baseline. • GATT Art. XX(g) (general exceptions – exhaustible natural resources): In respect of the US defence under Art. XX(g), the Appellate Body modified the Panel's reasoning and found that the measure was “related to” (i.e. “primarily aimed at”) the “conservation of exhaustible natural resources” and thus fell within the scope of Art. XX(g). However, the measure was still not", "keywords": ["energy & environment", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS8", "title": "JAPAN – ALCOHOLIC BEVERAGES II", "complainant": "Canada, European Communities, United States", "respondent": "Japan", "third_parties": [], "agreements": ["GATT Art. III"], "articles": [], "subject": "Japanese Liquor Tax Law that established a system of internal taxes applicable to all liquors at different tax rates depending on which category they fell within. The tax law at issue taxed shochu at ", "sector": "Other", "year": 1996, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1996", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel's finding that vodka was taxed in excess of shochu, in violation of Art. III:2, first sentence, accepting the Panel's interpretation that Art. III:2, first sentence requires an examination of the conformity of an internal tax measures by determining two elements: (i) whether the taxed imported and domestic products are like; and (ii) whether the taxes applied to the imported products are in excess of those applied to the like domestic products. • GATT Art. III:2 (national treatment – taxes and charge), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's finding that shochu and whisky, brandy, rum, gin, genever, and liqueurs were not similarly taxed so as to afford protection to domestic production, in violation of Art. III:2, second sentence. Modifying some of the Panel's reasoning, the Appellate Body clarifi", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS18", "title": "AUSTRALIA – SALMON", "complainant": "Canada", "respondent": "Australia", "third_parties": [], "agreements": ["SPS Arts. 5.1, 5.5 and 5.6"], "articles": [], "subject": "Australia's import prohibition of certain salmon from Canada.", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 5.1 (risk assessment): The Appellate Body, although reversing the Panel's finding because the Panel had examined the wrong measures (i.e. heat-treatment requirement), still found that the correct measure at issue – Australia's import prohibition – violated Art. 5.1 (and, by implication, Art. 2.2) because it was not based on a “risk assessment” requirement under Art. 5.1. • SPS Art. 5.5 (prohibition on discrimination and disguised restriction on international trade): The Appellate Body upheld the Panel's finding that the import prohibition violated Art. 5.5 (and, by implication Art. 2.3) as “arbitrary or unjustifiable” levels of protection were applied to several different yet comparable situations so as to result in “discrimination or a disguised restriction” (i.e. more strict restriction) on imports of salmon, compared to imports of other fish and fish products such as herring and finfish. • SPS Art. 5.6 (appropriate level of protection): The Appellate Body reversed the Pan", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS22", "title": "BRAZIL – DESICCATED COCONUT", "complainant": "Philippines", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I, II and VI"], "articles": [], "subject": "A countervailing duty Brazil imposed on 18 August 1995 based on an investigation initiated on 21 June 1994.", "sector": "Agriculture & Food", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Arts. I (most-favoured-nation treatment), II (schedules of concessions) and VI (anti-dumping and countervailing duties): The Appellate Body upheld the Panel's finding that GATT Arts. I, II and VI did not apply to the Brazilian countervailing duty measure at issue because it was based on an investigation initiated prior to 1 January 1995, the date that the WTO Agreement came into effect for Brazil. Specifically, the Panel found: (i) the subsidy rules in the GATT cannot apply independently of the ASCM; and (ii) non-application of the ASCM renders the subsidy rules in the GATT non-applicable. As for GATT Arts. I and II, they did not apply to this dispute because the claims under these provisions derived from the claims of inconsistency with Art. VI. • AA Art. 13 (due restraint): The Panel found that the exemption for countervailing duties contained in AA Art. 13 did not apply to a dispute based on a countervailing duty investigation initiated prior to the date the WTO Agreement cam", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS24", "title": "US – UNDERWEAR", "complainant": "Costa Rica", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6", "GATT Art. X:2"], "articles": [], "subject": "Quantitative import restriction imposed by the United States, as a transitional safeguard measure under ATC Art. 6.", "sector": "Safeguards", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6.10 (transitional safeguard measures – prospective application): The Appellate Body reversed the Panel's finding and concluded that in the absence of express authorization, the plain language of Art. 6.10 creates a presumption that a measure may be applied only prospectively, and thus may not be backdated so as to apply as of the date of publication of the importing Member's request for consultation. • ATC Art. 6.2 (transitional safeguard measures – serious damage and causation): The Panel refrained from making a finding on whether the United States demonstrated “serious damage” within the meaning of Art. 6.2, stating that ATC Art. 6.3 does not provide sufficient and exclusive guidance in this case. However, the Panel found that the United States had not demonstrated actual threat of serious damage, and therefore had violated Art. 6. The Panel also found that the United States failed to comply with its obligation to examine causality under Art. 6.2. • GATT Art. X:2 (trade r", "keywords": ["safeguards", "ATC", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS26", "title": "EC – HORMONES", "complainant": "United States, Canada", "respondent": "European Communities", "third_parties": [], "agreements": ["SPS Arts. 3 and 5"], "articles": [], "subject": "EC prohibition on the placing on the market and the importation of meat and meat products treated with certain hormones.", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• SPS Art. 3.1 (international standards): The Appellate Body rejected the Panel's interpretation and said that the requirement that SPS measures be “based on” international standards, guidelines or recommendations under Art. 3.1 does not mean that SPS measures must “conform to” such standards. • Relationship between SPS Arts. 3.1, 3.2 and 3.3 (harmonization): The Appellate Body rejected the Panel's interpretation that Art. 3.3 is the exception to Arts. 3.1 and 3.2 assimilated together and found that Arts. 3.1, 3.2 and 3.3 apply together, each addressing a separate situation. Accordingly, it reversed the Panel's finding that the burden of proof for the violation under Art. 3.3, as a provision providing the exception, shifts to the responding party. • SPS Art. 5.1 (risk assessment): While upholding the Panel's ultimate conclusion that the EC measure violated Art. 5.1 (and thus Art. 3.3) because it was not based on a risk assessment, the Appellate Body reversed the Panel's interpretation,", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS27", "title": "EC – BANANAS III (ARTICLE 21.5 – ECUADOR II)", "complainant": "United States, Ecuador", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. I, II 2 and XIII", "DSU Art. 21.5"], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2008, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2008", "summary_ar": "", "summary_en": "• GATT Art. XIII (non-discriminatory administration of quantitative restrictions): In the case initiated by Ecuador, the Appellate Body upheld the Panel's finding that, to the extent that the European Communities argued that it had implemented a suggestion pursuant to DSU Art. 19.1, the Panel was not prevented from conducting the assessment requested by Ecuador under DSU Art. 21.5. In both cases, the Appellate Body upheld, albeit for different reasons, the Panel's finding that the EC bananas import regime, in particular its duty-free tariff quota reserved for ACP countries, was inconsistent with Arts. XIII:1 and XIII:2. • GATT Art II (schedules of concessions): The Appellate Body reversed the Panel's finding that the waiver approved in November 2001 by the Ministerial Conference in Doha constituted a subsequent agreement between the parties extending the tariff quota concession for bananas listed in the European Communities' Schedule of Concessions beyond 31 December 2002, until the re", "keywords": ["agriculture & food", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS31", "title": "CANADA – PERIODICALS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. III, XI and XX"], "articles": [], "subject": "(i) Tariff Code 9958, which prohibited the importation into Canada of any periodical that was a “special edition” 2; (ii) the Excise Tax Act, which imposed, in respect of each split-run edition3 of a ", "sector": "Anti-Dumping", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions) and Art. XX(d) (exceptions – necessary to secure compliance with laws): The Panel found that Tariff Code 9958, which prohibited the importation of certain periodicals, violated Art. XI, and was not justified under Art. XX(d) because it could not be regarded as a measure to secure compliance with Canada's Income Tax Act. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Appellate Body reversed the Panel's finding that imported split-run periodicals and domestic non-split run periodicals were “like products” (Art. III:2, first sentence). The Appellate Body concluded that the Excise Tax Act was inconsistent with Art. III:2, second sentence because (i) imported split-run periodicals were “directly competitive or substitutable” with domestic non-split-run periodicals; (ii) imported and domestic products were not similarly taxed; and (iii) the tax was applied so as to afford protection to dome", "keywords": ["anti-dumping", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS33", "title": "US – WOOL SHIRTS AND BLOUSES", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ATC Arts. 6 and 2.4"], "articles": [], "subject": "Temporary safeguard measure imposed by the United States in the form of a quota on certain imports from India.", "sector": "Safeguards", "year": 1997, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "1997", "summary_ar": "", "summary_en": "• ATC Art. 6 (transitional safeguard measures): The Panel found that the United States violated Arts. 6.2 and 6.3 because it failed to meet the causation and serious damage (and threat of serious damage) requirements therein when imposing its transitional safeguard measure, in particular, by not examining the data relevant to the “woven wool shirts and blouses industry”, as opposed to the “woven shirts and blouses industry in general”. The Panel also considered the list of industry impact factors in Art. 6.3 to be a mandatory list: an investigating authority must demonstrate that it considered the relevance or otherwise of each of the listed items in Art. 6.3. Moreover, the Panel stated that under Art. 6.3, “some consideration and a relevant and adequate explanation have to be provided of how the facts as a whole support the conclusion that the termination is consistent with the requirements of the ATC”. • ATC Art. 2.4 (prohibition on new restrictions): The Panel found that, by violati", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS34", "title": "TURKEY – TEXTILES", "complainant": "India", "respondent": "Turkey", "third_parties": [], "agreements": ["GATT Arts. XI, XIII and XXIV", "ATC Art. 2.4"], "articles": [], "subject": "Turkey's quantitative import restrictions pursuant to the Turkey-EC customs union.", "sector": "Textiles", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Arts. XI (prohibition on quantitative restrictions) and XIII (non-discriminatory administration of quantitative restrictions): The Panel found that the quantitative restrictions at issue were inconsistent with Arts. XI and XIII. (Turkey did not deny this.) • ATC Art. 2.4 (prohibition on new restrictions): The Panel found that Turkey's measures were new restrictions, that did not exist at the time of the entry into force of the ATC, and, thus, were prohibited by Art. 2.4. • GATT Art. XXIV (regional trade agreements): The Appellate Body agreed with the Panel's ultimate conclusion that Turkey's measures were not justified under Art. XXIV because there were alternatives available to Turkey that would have met the requirements of Art. XXIV:8(a), which were necessary to form the customs union, other than the adoption of the quantitative restrictions. The Appellate Body, therefore, modified the Panel's legal reasoning and concluded that to determine whether a measure found inconsistent", "keywords": ["textiles", "GATT", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS44", "title": "JAPAN – FILM", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["GATT Arts. XXIII:1(b), III:4 and X:1"], "articles": [], "subject": "Actions by Japan affecting the distribution, offering for sale, and internal sale of imported consumer photographic film and paper, in particular, (i) distribution measures; (ii) restrictions on large", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XXIII:1(b) (non-violation claim): The Panel found that the United States failed to demonstrate that the measures at issue nullified or impaired benefits accruing to the United States within the meaning of Art. XXIII:1(b). The Panel considered that a complaining party must demonstrate three elements under Art. XXIII:1(b): (i) application of a measure by a WTO Member; (ii) a benefit accruing under the relevant agreement: and (iii) nullification or impairment of the benefit as the result of the application of the measure. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the distribution measures were generally origin-neutral and did not have a disparate impact on imported film or paper. The Panel therefore found that the United States had not proved that the distribution measures were inconsistent with Art. III:4. • GATT Art. X:1 (trade regulations – prompt publication): The Panel considered that the publication requirement in Art. X", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS46", "title": "BRAZIL – AIRCRAFT (ARTICLE 21.5 – CANADA)", "complainant": "Canada", "respondent": "Brazil", "third_parties": [], "agreements": ["ASCM Art. 4.7 and Annex I, item (k)"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2000, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2000", "summary_ar": "", "summary_en": "• ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): The Appellate Body upheld the Panel's findings that Brazil was in violation of Art. 4.7 as it had not withdrawn the export subsidies for regional aircraft within 90 days of the adoption of the original panel and Appellate Body reports. The Appellate Body stated that Brazil's argument that it was continuing to make payments under letters of commitment (private contractual obligations under domestic law), which had been made before the expiry of the 90‑day period of implementation, was not an adequate defence against the implementation of DSB recommendations. • ASCM Annex I, Illustrative List of Export Subsidies, item (k): The Appellate Body upheld the Panel's conclusion and found that Brazil had failed to demonstrate that the PROEX payments were not used to secure a material advantage in the field of export credit terms within the meaning of item (k) because Brazil had not identified an appropriate “market benchmark” for", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS50", "title": "INDIA – PATENTS (US)", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Art. 70.8 and 70.9"], "articles": [], "subject": "(i) India's “mailbox rule” – under which patent applications for pharmaceutical and agricultural chemical products could be filed; and (ii) the mechanism for granting exclusive marketing rights to suc", "sector": "Intellectual Property", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Appellate Body upheld the Panel's finding that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Appellate Body found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the administrative instructions could be rejected by the court under the contradictory mandatory provisions of the existing Indian laws: the Patents Act of 1970. • TRIPS Art. 70.9 (exclusive marketing rights): The Appellate Body agreed with the Panel that there was no mechanism in place in India for the grant of exclusive marketing rights for the products covered by Art. 70.8(a) and thus Art. 70.9 was violated.", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS54", "title": "INDONESIA – AUTOS", "complainant": "European Communities, United States, Japan", "respondent": "Indonesia", "third_parties": [], "agreements": ["TRIMs Art. 2.1", "GATT Arts. I:1 and III:2", "ASCM Arts. 5(c), 6, 27.9 and 28"], "articles": [], "subject": "(i) “The 1993 Programme” that provided import duty reductions or exemptions on imports of automotive parts based on the local content percent; and (ii) “The 1996 National Car Programme” that provided ", "sector": "Subsidies & Anti-Subsidy", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIMs Agreement Art. 2.1 (local content requirement): 2 The Panel found the 1993 Programme to be in violation of Art. 2.1 because (i) the measure was a “trade-related investment”3 measure; and (ii) the measure, as a local content requirement, fell within para. 1 of the Illustrative List of TRIMs in the Annex to the TRIMs Agreement, which sets out trade-related investment measures that are inconsistent with national treatment obligation under GATT Art. III:4. • GATT Art. III:2, first and second sentences (national treatment – taxes and charges): The Panel found that the sales tax benefits under the measures violated both Art. III:2, first and second sentences. The Panel noted that under the Indonesian car programmes, an imported motor vehicle would be taxed at a higher rate than a like domestic vehicle in violation of Art. III:2, first sentence, and also, any imported vehicle would not be taxed similarly to a directly competitive or substitutable domestic car due to these Indonesian c", "keywords": ["subsidies & anti-subsidy", "TRIMs", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS56", "title": "ARGENTINA – TEXTILES AND APPAREL", "complainant": "United States", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. II and VIII"], "articles": [], "subject": "(i) Argentina's system of minimum specific import duties, known as “DIEM”, on textiles and apparel (under which textiles and apparel were subject to either a 35 per cent ad valorem duty or a minimum s", "sector": "Textiles", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II (schedules of concessions): The Appellate Body found Argentina's measure was, in fact, inconsistent with Art. II:1(b). It held that “the application of a type of duty different from the type provided for in a Member's Schedule is inconsistent with GATT Art. II:1(b), first sentence, to the extent that it results in ordinary customs duties being levied in excess of those provided for in that Member's Schedule.” In this case, the Appellate Body concluded that “the structure and design of the Argentine system is such that for any DIEM ... the possibility remains that there is a ‘break-even’ price below which the ad valorem equivalent of the customs duty collected is in excess of the bound ad valorem rate of 35 per cent.” • GATT Art. VIII (fees and formalities): The Appellate Body upheld the Panel's findings that the statistical tax on imports violated Argentina's obligations under Art. VIII:1(a) “to the extent it results in charges being levied in excess of the approximate c", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS58", "title": "US – SHRIMP", "complainant": "India, Malaysia, Pakistan, Thailand", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. XI and XX"], "articles": [], "subject": "US import prohibition of shrimp and shrimp products from non-certified countries (i.e. countries that had not used a certain net in catching shrimp).", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel found that the US prohibition, based on Section 609, on imported shrimp and shrimp products violated Art. XI. The United States apparently conceded the measure's violation of Art. XI because it did not put forward any defending arguments in this regard. • GATT Art. XX(g) (general exceptions – exhaustible natural resources): The Appellate Body held that although the US import ban was related to the conservation of exhaustible natural resources and, thus, covered by an Art. XX(g) exception, it could not be justified under Art. XX because the ban constituted “arbitrary and unjustifiable” discrimination under the chapeau of Art. XX. In reaching this conclusion, the Appellate Body reasoned, inter alia, that in its application the measure was “unjustifiably” discriminatory because of its intended and actual coercive effect on the specific policy decisions made by foreign governments that were Members of the WTO. The measure", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS60", "title": "GUATEMALA – CEMENT I", "complainant": "Mexico", "respondent": "Guatemala", "third_parties": [], "agreements": ["DSU Art. 6.2", "ADA Art. 17.4 (Art. 5)"], "articles": [], "subject": "Guatemala's anti-dumping investigation (both the initiation and various decisions and conduct of the Ministry).", "sector": "Anti-Dumping", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1998", "summary_ar": "", "summary_en": "• DSU Art. 6.2 and ADA Art. 17.4 (requirements of panel request): The Appellate Body, reversing the Panel, concluded that Mexico had failed to identify in its panel request the “specific measures at issue” in accordance with DSU Art. 6.2 and ADA Art. 17.4, i.e. one of the three measures to be specified in a dispute involving anti-dumping investigations: (i) a definitive antidumping duty, (ii) the acceptance of a price undertaking, or (iii) a provisional anti-dumping measure. According to the Appellate Body, the special dispute settlement rules in the ADA and the DSU provisions together create a “comprehensive, integrated dispute settlement system” rather than the former replacing the more general rules in the DSU as the Panel had erroneously found. The Appellate Body rejected the Panel's reasoning that the term “measure” under DSU Art. 6.2 should be interpreted broadly, and clarified that both identification of “measure” and identification of the alleged “violations” are separately req", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS62", "title": "EC – COMPUTER EQUIPMENT", "complainant": "United States", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II:1"], "articles": [], "subject": "The European Communities' application of tariffs on local area networks: (LAN) equipment and multimedia personal computers (PCs) in excess of those provided for in the EC Schedules through changes in ", "sector": "Other", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedule of concessions – LAN): The Appellate Body reversed the Panel's finding of a violation by the European Communities of Art. II:1 with respect to LAN equipment on the basis of the Panel's erroneous legal reasoning and consideration of only selective evidence. In this regard the Appellate Body rejected the Panel's finding that a tariff concession in the Schedule can be interpreted in light of an exporting Member's “legitimate expectations” – a concept relevant to a nonviolation complainant under GATT Art. XXIII:1(b) – in the context of a violation complaint. Rather, the Appellate Body found that a tariff concession provided for in the Member's Schedule should be interpreted according to the general rules of treaty interpretation set out in Arts. 31 and 32 of the VCLT2; Moreover, the Appellate Body said that the Panel should have further examined the following: the Harmonized System and its Explanatory Notes as context in interpretation of the terms of the Schedul", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS69", "title": "EC – POULTRY", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. XIII, X"], "articles": [], "subject": "European Communities' tariff rate quota (TRQ) system incorporated into EC Schedule LXXX with respect to frozen poultry and the European Communities' licensing requirements for importers of the product", "sector": "Agriculture & Food", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• GATT Art. XIII:2 (non-discriminatory administration of quantitative restrictions): The Appellate Body upheld the Panel's finding that the TRQ must be administered on a non-discriminatory basis – as opposed to it being awarded exclusively to Brazil – based on the text of the EC Schedule LXXX and pursuant to Art. XIII, and thus, the European Communities had acted consistently with its WTO obligations. The Appellate Body also upheld the Panel's finding that, even when a TRQ is the result of an Art. XXVIII compensation negotiation, it must be administered in a non-discriminatory manner (total imports, including those from non-Members). The Appellate Body also agreed with the Panel that TRQ shares must be calculated on the basis of “total imports”, including imports coming from non-Members, and thus, the European Communities acted consistently with Art. XIII:2 by including imports from non-Members in its TRQ calculation. • GATT Art. X (publication and administration of trade regulation): ", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS70", "title": "CANADA – AIRCRAFT", "complainant": "Brazil", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1 and 4.7"], "articles": [], "subject": "Canadian measures providing various forms of financial support to the domestic civil aircraft industry.", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (definition of a subsidy): The Panel found that a “financial contribution” confers a “benefit” and constitutes a subsidy under Art. 1 when provided on terms more advantageous than those otherwise available to the recipient on the market. The Appellate Body, while upholding this finding, concluded that the word “conferred”, in conjunction with “thereby”, calls for an inquiry into what was conferred on the recipient, not an inquiry into the cost to the government as argued by Canada. • ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): The Appellate Body upheld the Panel's finding that contingency exists if there is a relationship of conditionality or dependence between the grant of the subsidy and the anticipated exportation or export earnings. • Examination of Canada's individual measures (as such/as applied distinction for discretionary and mandatory measures): The Panel concluded that the EDC programme as such was discretionary legislation and, upon examinati", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS75", "title": "KOREA – ALCOHOLIC BEVERAGES", "complainant": "European Communities, United States", "respondent": "Korea", "third_parties": [], "agreements": ["GATT Art. III:2, second sentence"], "articles": [], "subject": "Korea's tax regime for alcoholic beverages, which imposed different tax rates for various categories of distilled spirits.", "sector": "Other", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's conclusion that the Korean tax measures at issue were inconsistent with Art. III:2, second sentence: More specifically, the Appellate Body upheld the Panel's findings that the products at issue were “directly competitive or substitutable” within the meaning of Art. III:2, second sentence and that Korea's tax measures on alcoholic beverages were applied “so as to afford protection” to domestic production within the meaning of Art. III:2, second sentence. On the question of the interpretation and application of the term “directly competitive or substitutable product”, the Appellate Body upheld the Panel's approach: (i) the Panel correctly considered evidence of “present direct competition”, not the future evolution of the market, by referring to the potential for the products to compete in a market free of protection because i", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS76", "title": "JAPAN – AGRICULTURAL PRODUCTS II", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7, 5.6 and 5.1"], "articles": [], "subject": "Varietal testing requirement (Japan's Plant Protection Law), under which the import of certain plants was prohibited because of the possibility of their becoming potential hosts of codling moth.", "sector": "Agriculture & Food", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1999", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that Japan's varietal testing requirement was maintained without sufficient scientific evidence in violation of Art. 2.2.3 • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the varietal testing requirement was not justified under Art. 5.7 because Japan did not meet all the requirements for the adoption and maintenance of a provisional SPS measure as set out in Art. 5.7. • SPS Art. 5.6 (appropriate level of protection – alternative measures): Having found that the United States, as a complainant, did not claim and, therefore, could not have established a prima facie case of Japan's inconsistency with the existence of an alternative measure (determination of sorption levels) under Art. 5.6, the Appellate Body reversed the Panel's finding that Japan acted inconsistently with Art. 5.6. Then, as to the alternative measure proposed by the United States – i.e. ", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS79", "title": "INDIA – PATENTS (EC)", "complainant": "European Communities", "respondent": "India", "third_parties": [], "agreements": ["TRIPS Arts. 70.8 and 70.9"], "articles": [], "subject": "(i) The insufficiency of the legal regime – India's “mailbox rule” – under which patent applications for pharmaceutical and agricultural chemical products could be filed; and (ii) the lack of a mechan", "sector": "Intellectual Property", "year": 1998, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "1998", "summary_ar": "", "summary_en": "• TRIPS Art. 70.8 (filing of patent application): The Panel held that India's filing system based on “administrative practice” for patent applications for pharmaceutical and agricultural chemical products was inconsistent with Art. 70.8. The Panel found that the system did not provide the “means” by which applications for patents for such inventions could be securely filed within the meaning of Art. 70.8(a), because, in theory, a patent application filed under the current administrative instructions could be rejected by the court under the contradictory mandatory provisions of the pertinent Indian law – the Patents Act of 1970. • TRIPS Art. 70.9 (exclusive marketing rights): The Panel found that there was no mechanism in place in India for the grant of “exclusive marketing rights” for pharmaceutical and agricultural chemical products and thus Art. 70.9 had been violated. 1 India – Patent Protection for Pharmaceutical and Agricultural Chemical Products (complaint by the European Communi", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS87", "title": "CHILE – ALCOHOLIC BEVERAGES", "complainant": "European Communities", "respondent": "Chile", "third_parties": [], "agreements": ["GATT Art. III:2"], "articles": [], "subject": "Chile's tax measures that imposed an excise tax at different rates – depending on the type of product (pisco, whisky, etc.) under the “Transitional System” and according to the degree of alcohol conte", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): The Appellate Body upheld the Panel's finding that Chile's new tax regime for alcoholic beverages violated the national treatment principle under Art. III:2, second sentence. (Chile's appeal was only in regard to the new regime.) The Panel found both Chile's transitional and new tax regimes inconsistent with Art. III:2, second sentence. (“not similarly taxed”): The Appellate Body agreed with the Panel that imported distilled spirits and Chilean pisco, as directly competitive and substitutable products, were not similarly taxed since the tax burden (47 per cent) on most of imported products (95 per cent of imports) would be heavier than the tax burden (27 per cent) on most of the domestic products (75 per cent of domestic production). The Appellate Body took the view that the relevant comparison between imported and domestic products had to be made based on a com", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS99", "title": "US – DRAMS", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 11, 2.2, 6.6 and 5.8"], "articles": [], "subject": "United States Department of Commerce (USDOC) regulation (namely, the “three zeroes” rules)2, both as applied in the DRAMS third administrative review at issue and as such, and other aspects of the thi", "sector": "Anti-Dumping", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ADA Art. 11.2 (review of anti-dumping duties – the “likely” standard): The Panel found for Korea and held that the “not likely” standard in the US regulation (as quoted in footnote 2 below), as such, is inconsistent with Art. 11.2 (“likely” standard) because a failure to find that an exporter is “not likely” to dump does not necessarily lead to the conclusion that this exporter is therefore “likely” to dump. The Panel considered that because there are situations where the not “not likely” standard is satisfied but the “likely” standard is not, the “not likely” criterion fails to provide a “demonstrable basis for consistently and reliably determining that the likelihood criterion is satisfied”. The Panel also found that because the final results of the third administrative review in the DRAMS case were based on a USDOC determination under that regulation, those results, as applied, were inconsistent with Art. 11.2 as well. • ADA Art. 2.2.1.1 (dumping determination – acceptance of data", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS103", "title": "CANADA – DAIRY (ARTICLE 21.5 – NEW ZEALAND AND US)", "complainant": "New Zealand, United States", "respondent": "Canada", "third_parties": [], "agreements": [], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2001, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2001", "summary_ar": "", "summary_en": "• AA Art. 9.1(c) (export subsidies – payments financed by virtue of governmental action): On the question of whether the Canadian measures were “payments on the export of an agricultural product that are financed by virtue of governmental action” and thus constituted a subsidy under Art. 9.1(c) (which was made in excess of its export subsidy and quantity commitments in violation of Arts. 3.3 and 8 thereof), the Appellate Body reversed the Panel's legal findings as follows. (The Appellate Body, however, did not complete the analyses based on the correct legal standard.)3 (“payments”) The Appellate Body held first that neither prices for milk destined for the domestic market nor world market prices could serve as the appropriate basis for determining whether prices charged for export sales constituted a “payment” within the meaning of Art. 9.1 (c). The Appellate Body, while holding that the “average total cost of production” was the appropriate standard for determining whether export sal", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS108", "title": "US – FSC (ARTICLE 21.5 – EC II)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 4.7"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2006, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2006", "summary_ar": "", "summary_en": "• ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): Having concluded that the “recommendation under Art. 4.7 remains in effect until the Member concerned has fulfilled its obligation by fully withdrawing the prohibited subsidy”, the Appellate Body upheld the Panel's finding that “to the extent that the United States, by enacting Section 101 of the Jobs Act, maintains prohibited FSC and ETI subsidies through the transitional and grandfathering measures, it continues to fail to implement fully the operative DSB recommendations and rulings to withdraw the prohibited subsidies and to bring its measures into conformity with its obligations under the relevant covered agreements.” In this regard, it agreed with the Panel that “the relevant recommendations adopted by the DSB in the original proceedings in 2000, and those in the first and these second Art. 21.5 proceedings, form part of a continuum of events relating to compliance with the recommendations and rulings of the DSB i", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS114", "title": "CANADA – PHARMACEUTICAL PATENTS", "complainant": "European Communities", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 27, 28 and 30"], "articles": [], "subject": "Certain provisions under Canada's Patent Act: (i)”regulatory review provision (Sec. 55.2(1))” 2; and (ii)”stockpiling provision (Sec. 55.2(2))” that allowed general drug manufacturers to override, in ", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "Stockpiling provision • TRIPS Arts. 28.1 (patent owner rights) and 30 (exceptions): (Canada practically conceded that the stockpiling provision violated Art. 28.1, which sets out exclusive rights granted to patent owners.) Concerning Canada's defence under Art. 30, the Panel found that the measure was not justified under Art. 30 because there were no limitations on the quantity of production for stockpiling which resulted in a substantial curtailment of extended market exclusivity, and, thus, was not “limited” as required by Art. 30. Accordingly, the Panel concluded that the stockpiling provision was inconsistent with Art. 28.1 as it constituted a “substantial curtailment of the exclusionary rights” granted to patent holders. Regulatory review provision • TRIPS Arts. 28.1 (patent owner rights) and 30 (exceptions): (Canada also practically conceded on the inconsistency of the provision with Art. 28.1) The Panel found that Canada's regulatory review provision was justified under Art. 30 ", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS122", "title": "THAILAND – H-BEAMS", "complainant": "Poland", "respondent": "Thailand", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 17.6"], "articles": [], "subject": "Thailand's definitive anti-dumping determination.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 5 (initiation of investigation): The Panel rejected Poland's claim that the Thai authorities' initiation of the investigation could not be justified due to the insufficiency of evidence originally contained in the application. The Panel considered that the application need not contain analysis, but only information. The Panel also rejected Poland's claim that Thailand violated Art. 5.5 by failing to provide a written notification of the filing of application for initiation of investigation. The Panel considered that a formal meeting could satisfy the requirement. • ADA Art. 2.2 (dumping determination – constructed normal value): As the Panel found that, (i) for the purpose of calculating a dumping margin under Art. 2.2, Thailand used the narrowest product category that included the like product; and (ii) that no separate reasonability test was required in choosing a profit figure for constructed normal value, the Panel concluded that Thailand had not violated Art. 2.2. • ADA", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS126", "title": "AUSTRALIA – AUTOMOTIVE LEATHER II", "complainant": "United States", "respondent": "Australia", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1(a) and 4.7"], "articles": [], "subject": "Australian government's assistance (“grant contract” ($A 30 million) and “loan contract” ($A 25 million)) to Howe, a wholly-owned subsidiary of Australian Leather Upholstery Pty. Ltd., owned by Austra", "sector": "Subsidies & Anti-Subsidy", "year": 1999, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "1999", "summary_ar": "", "summary_en": "• ASCM Art. 3.1(a) (prohibited subsidies – export subsidies): As for the grant contract, the Panel found that the payments under the grant contract were subsidies prohibited under Art. 3.1(a), on the ground that the payments concerned were in fact “tied to” export performance. In respect of the loan contract, the Panel concluded that the payments under the loan contract did not violate Art. 3.1(a) because there was nothing in the terms of the loan contract itself that suggested a “specific link” to actual or anticipated exportation or export earnings. • ASCM Art. 4.7 (recommendation to withdraw a prohibited subsidy): The Panel recommended, in accordance with Art. 4.7, that Australia withdraw the prohibited subsidies within a 90-day period, which would run from the date of adoption of the report by the DSB.", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS136", "title": "US – 1916 ACT", "complainant": "European Communities, Japan", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI", "ADA Arts. 1, 4, 5 and 18"], "articles": [], "subject": "United States' Anti-Dumping Act of 1916, which provided for, inter alia, a private right of action, the remedy of treble damages for private complaints and the possibility of criminal penalties in res", "sector": "Anti-Dumping", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. VI and ADA (applicability): The Appellate Body upheld the Panel's finding that GATT Art. VI and the ADA applied to the 1916 Act. Art. VI applies to action taken in response to situations involving dumping and the 1916 Act provided for specific action to be taken in situations that present the constituent elements of dumping within the meaning of that provision. • GATT Art. VI and ADA (substantive violations): 2 The Appellate Body upheld the Panel's findings on the following claims: the 1916 Act was inconsistent with: (i) GATT Art. VI (anti-dumping duties) which, read in conjunction with the ADA, limits the permissible responses to dumping to definitive anti‑dumping duties, provisional measures and price undertakings; (ii) GATT Art. VI:1 (anti-dumping duties – conditions) because it did not require a finding of “material injury”; (iii) ADA Art. 4 (and 5 as well in case of Japan): (definition of domestic industry) because the Act did not require that a complaint be made “on b", "keywords": ["anti-dumping", "GATT", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS139", "title": "CANADA – AUTOS", "complainant": "European Communities, Japan", "respondent": "Canada", "third_parties": [], "agreements": ["ASCM Arts. 1, 3 and 4.7", "GATS Arts. I and II", "GATT Arts. I and III"], "articles": [], "subject": "Canada's import duty exemption for imports by certain manufacturers, in conjunction with the Canadian Value Added (CVA) requirements and the production to sales ratio requirements.", "sector": "Services", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GATT Art. I (most-favoured-nation treatment): The Appellate Body upheld the Panel's finding that the duty exemption was inconsistent with the most-favoured-nation treatment obligation under Art. I:1 on the ground that Art. I:1 covers not only de jure but also de facto discrimination and that the duty exemption at issue in reality was given only to the imports from a small number of countries in which an exporter was affiliated with eligible Canadian manufacturers/importers. The Panel rejected Canada's defence that Art. XXIV allows the duty exemption for NAFTA members (Mexico and the United States), because it found that the exemption was provided to countries other than the United States and Mexico and because the exemption did not apply to all manufacturers from these countries. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the CVA requirements forcing the use of domestic materials to be eligible for tax exemption resulted in “less favo", "keywords": ["services", "ASCM", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS141", "title": "EC – BED LINEN (ARTICLE 21.5 – INDIA)", "complainant": "India", "respondent": "European Communities", "third_parties": [], "agreements": ["ADA Arts. 3 and 15"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2003, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.2 (injury determination – volume of dumped imports): The Appellate Body reversed the Panel's findings on this issue and concluded that the European Communities' consideration of all imports from un-examined producers as dumped for the purposes of the injury analysis was based on a presumption not supported by positive evidence. Therefore, the Appellate Body held that the European Communities acted inconsistently with Arts. 3.1 and 3.2 as it had not determined the “volume of dumped imports” on the basis of “positive evidence” and an “objective assessment”. • ADA Arts. 3.1 and 3.4 (injury determination – injury factors): The Panel rejected India's claim that the European Communities did not have information on the economic factors and indices in Art. 3.4 (i.e. inventories and capacity utilization). The Panel concluded that the European Communities had collected data on these factors and that it did conduct an overall reconsideration and analysis of the facts with re", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS146", "title": "INDIA – AUTOS", "complainant": "European Communities, United States", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. III, XI and XVIII:B", "DSU Art. 19.1"], "articles": [], "subject": "India's (i) indigenization (local content) requirement; and (ii) trade balancing requirement (exports value = imports value) imposed on its automotive sector.2", "sector": "Automotive", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "Indigenization requirement • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel concluded that the measure violated Art. III:4, as the indigenization requirement modified the conditions of competition in the Indian market “to the detriment of imported car parts and components”. Trade balancing requirement • GATT Art. XI:1 (prohibition on quantitative restrictions): Having found that “any form of limitation imposed on, or in relation to importation constitutes a restriction on importation within the meaning of Art. XI”, the Panel found that India's trade balancing requirement, which limited the amount of imports in relation to an export commitment, acted as a restriction on importation within the meaning of Art. XI:1, and thus violated Art. XI:1. The Panel also found that India failed to make a prima facie case that this requirement was justified under the balance-of-payments provisions of Art. XVIII:B. • GATT Art. III:4 (national treatment – domestic laws a", "keywords": ["automotive", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS152", "title": "US – SECTION 301 TRADE ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Art. 23.2(a) and (c)"], "articles": [], "subject": "US legislation (i.e. Sections 301-310 of the Trade Act of 1974) authorizing certain actions by the Office of the United States Trade Representative (USTR), including the suspension or withdrawal of co", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• DSU Art. 23.2(a) (prohibition on unilateral determinations – Section 304): Based on the terms of Art. 23.2(a), the Panel first set out that it is for the WTO, through the DSU process, and not an individual WTO Member, to determine that a measure is inconsistent with WTO obligations. The Panel then concluded that Section 304 was “not inconsistent” with US obligations under Art. 23.2(a) because, while the statutory language of Section 304 in itself constituted a serious threat that unilateral determinations contrary to Art. 23.2(a) might be taken, the United States had (i) lawfully removed this threat by the “aggregate effect of the Statement of Administrative Action ('SAA')” and (ii) made a statement before the Panel that it would render determinations under Section 304 in conformity with its WTO obligations. In this regard, the Panel added the caveat, however, that should the United States repudiate or remove in any way its undertakings contained in the SAA and confirmed in statement", "keywords": ["other", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS155", "title": "ARGENTINA – HIDES AND LEATHER", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. III:2, X, XI and XX"], "articles": [], "subject": "(i) Argentine regulations by which representatives of the Argentine leather tanning industry were present during the customs clearance process for bovine hides export; and (ii) advance tax payments th", "sector": "Other", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2001", "summary_ar": "", "summary_en": "Regulations on export control • GATT Art. XI:1 (prohibition on quantitative restrictions): The Panel rejected the EC claim that the Argentine regulations on export procedures were an export restriction prohibited by Art. XI. The European Communities had failed to meet its burden of proving that the presence of the tanners' representatives during customs procedures, along with the disclosure of information about the slaughterhouses and any possible abuse of this information, was an export restriction under Art. XI:1. • GATT Art. X:3(a) (trade regulations – uniform, impartial and reasonable administration): Having concluded that Art. X:3(a) applied to the measure at issue, as (i) the substance of the measure at issue was “administrative in nature” and did not establish substantive customs rules for enforcement of export laws and (ii) the measure was a law of “general application,” rather than a law applying only to the specific shipments of products, the Panel found that the measure was ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS163", "title": "KOREA – PROCUREMENT", "complainant": "United States", "respondent": "Korea", "third_parties": [], "agreements": ["GPA Arts. I and XXII:2"], "articles": [], "subject": "", "sector": "Other", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• GPA Art. I (scope of Korea's GPA Appendix I commitment): The Panel found, based on the terms of Korea's concessions in its GPA Schedule and the supplementary negotiating history of the Schedule, that the entities allegedly responsible for IIA procurement – i.e. NADG or KAA – were not entities covered by Korea's GPA schedule, and thus concluded that the IIA project was not covered by Korea's commitments under the GPA. • GPA Art. XXII:2 (non-violation nullification or impairment): Regarding the US non-violation claim under GPA Art. XXII:2, which was based on the frustration of reasonably expected benefits from alleged promises made during “negotiations” rather than nullification or impairment of actual concessions made, the Panel considered that the concept of non-violation could be extended to contexts other than the traditional approach. As such, the Panel decided to examine the US claim “within the framework of principles of international law (Art. 48 of the VCLT) which are generall", "keywords": ["other", "GPA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS170", "title": "CANADA – PATENT TERM", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["TRIPS Arts. 33 and 70"], "articles": [], "subject": "Canada's Patent Act, Section 45, which provided the length of the patent protection for patents filed before 1 October 1989 (Old Act).2", "sector": "Intellectual Property", "year": 2000, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2000", "summary_ar": "", "summary_en": "• TRIPS Art. 70.1 and 70.2 (protection of existing subject matter): (Art. 70.2) Having found that “a treaty applies to existing rights, even when those rights result from 'acts which occurred' before the treaty entered into force” and Art. 70.2 applies to existing inventions (rights) under Old Act patents whose patents were granted (acts) before the date of entry into force of the TRIPS Agreement, the Appellate Body concluded that Canada was bound by the obligation to provide existing patented inventions with a patent term of not less than 20 years from the filing date as required under Art. 33. (Art. 70.1) The Appellate Body also upheld the Panel's finding that Art. 70.1, limiting the retroactive application of the TRIPS Agreement, did not exclude Old Act patents from the scope of the TRIPS Agreement, as “acts” and the “rights created by such acts” should be distinguished and the limitation under Art. 70.1 applies to acts related to the patent, not rights provided by patent itself. • ", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS176", "title": "US – SECTION 211 APPROPRIATIONS ACT", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["TRIPS Arts. 2, 3, 4, 15, 16 and 42"], "articles": [], "subject": "Section 211 of the US Omnibus Appropriations Act of 1998, prohibiting those having an interest in trademarks/trade names related to certain businesses or assets confiscated by the Cuban government fro", "sector": "Intellectual Property", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "Section 211(a)(1) • TRIPS Art. 15 (trademarks – protectable subject matter) and Art. 2.1 (Paris Convention Art. 6quinquies A(1): As Art. 15.1 embodies a definition of a trademark and sets forth only the eligibility criteria for registration as trademarks (but not an obligation to register “all” eligible trademarks), the Appellate Body found that Section 211(a)(1) was not inconsistent with Art. 15.1, as the regulation concerned “ownership” of a trademark. The Appellate Body also agreed with the Panel that Section 211(a)(1) was not inconsistent with Paris Convention Art. 6quinquies A(1), which addressees only the “form” of a trademark, not ownership. Sections 211(a)(2) and (b) • TRIPS Arts. 16.1 (trademarks – exclusive rights of the owners and limited exceptions) and 42 (civil and administrative procedures and remedies): As there are no rules determining the “owner” of a trademark (i.e. discretion left to individual countries), the Appellate Body found that Section 211(a)(2) and (b) were", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS179", "title": "US – STAINLESS STEEL", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2"], "articles": [], "subject": "Definitive anti-dumping duties imposed by the United States on certain steel imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 2.4.1 (dumping determination – currency conversion): Having found that where the prices being compared (i.e. export price and normal price) were already in the same currency, “currency conversion” was not required and thus not permissible under Art. 2.4.1, the Panel concluded that the United States acted inconsistently with Art. 2.4.1 by making a currency conversion that was not required in the Sheet investigation, but did not act inconsistently with Art. 2.4.1 in the Plate investigation. • ADA Art. 2.4 (dumping determination – unpaid sales): In calculating a “constructed export price”, the Panel found that Members are permitted to make only those adjustments identified in Art. 2.4 (i.e. allowances for costs, including duties and taxes, incurred between importation and resale), and thus concluded that the United States improperly calculated a constructed export price in respect of sales made through an affiliated importer by deducting the unpaid sales (from bankrupted buyer)", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS184", "title": "US – HOT-ROLLED STEEL", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6 and 9"], "articles": [], "subject": "US definitive anti-dumping duties on certain imports.", "sector": "Metals & Mining", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 (evidence – facts available): The Appellate Body upheld the Panel's findings that the United States acted inconsistently with Art. 6.8 in applying facts available to exporters, as the United States Department of Commerce (USDOC) had rejected certain information submitted after the deadline without considering whether it was still submitted within a reasonable period of time. The Appellate Body upheld the Panel's finding that the United States acted inconsistently with Art. 6.8 and Annex II when it applied “adverse” facts available to an exporter in respect of certain resale prices by its affiliated company despite the difficulties faced by that exporter in obtaining the requested information and USDOC's reluctance to take any step to assist it. • ADA Art. 9.4 (imposition of anti-dumping duties – “all others” rate): Having found that margins established based in part on facts available are to be excluded in calculating an “all others” rate under Art. 9.4, the Appellate Bo", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS189", "title": "ARGENTINA – CERAMIC TILES", "complainant": "European Communities", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2 and 6"], "articles": [], "subject": "Argentina's definitive anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ADA Art. 6.8 and Annex II (evidence – facts available): The Panel found that Art. 6.8, in conjunction with Annex II(6), requires an investigating authority to inform the party supplying information on the reasons why evidence or information is not accepted, to provide an opportunity to provide further explanation within a reasonable period, and to give, in any published determinations, the reasons for the rejection of evidence of information. The Panel then concluded that the Argentine investigating authority (DCD) acted inconsistently with these requirements under Art. 6.8 by failing to explain its evaluation of the information that led it to disregard in large part the information provided by exporters, resorting instead to the use of facts available. The Panel also rejected Argentina's various justifications for relying on facts available. • ADA Art. 6.10 (evidence – individual dumping margins): The Panel found that the DCD acted inconsistently with Art. 6.10 by imposing the same ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS192", "title": "US – COTTON YARN", "complainant": "Pakistan", "respondent": "United States", "third_parties": [], "agreements": ["ATC Art. 6"], "articles": [], "subject": "Transitional safeguard remedy imposed by the United States under the ATC on certain imports.", "sector": "Safeguards", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ATC Art. 6.2 (transitional safeguard measure – scope of domestic industry): The Appellate Body upheld the Panel's ultimate conclusion that the United States acted inconsistently with Art. 6.2 by excluding from the scope of the domestic industry captive production of yarn (i.e. yarn produced by and processed and consumed within integrated producers for their own use and processing), which was found to be “directly competitive” with yarn offered for sale on the merchant (open) market. In this regard, the Appellate Body considered the term “directly competitive” to suggest a focus on the competitive relationship of products, including not only actual but also “potential competition”. • ATC Art. 6.4 (transitional safeguard measures – attribution of serious damage): The Appellate Body found that (i) Art. 6.4 requires a “comparative analysis” when there is more than one Member from whom imports have shown a sharp and substantial increase and (ii) under such a comparative analysis, “the ful", "keywords": ["safeguards", "ATC"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS194", "title": "US – EXPORT RESTRAINTS", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 1.1"], "articles": [], "subject": "Treatment of “export restraints” 2 under US countervailing duty (CVD) law (statute), in light of the relevant Statement of Administrative Action (SAA) and Preamble to CVD Regulations, and relevant Uni", "sector": "Subsidies & Anti-Subsidy", "year": 2001, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2001", "summary_ar": "", "summary_en": "• ASCM Art. 1.1 (a): (1): (iv) (definition of a subsidy – financial contribution): The Panel first concluded that an “export restraint” cannot constitute government-entrusted or government-directed provision of goods in the sense of subpara. (iv) of Art. 1.1(a)(1), and thus does not constitute a “financial contribution” within the meaning of Art. 1.1. According to the Panel, the “entrusts or directs” standard of subpara. (iv) requires an “explicit and affirmative action of delegation or command”, rather definition of a subsidy – than mere government intervention in the market by itself which leads to a particular result or effect. • Nature of the US law at issue (mandatory vs discretionary): To answer the ultimate question of whether the United States was in violation of the ASCM, the Panel examined whether the US law at issue “required” the USDOC (i.e. executive branch of the government) to treat export restraints as “financial contributions” in CVD investigations. Having found that t", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS202", "title": "US – LINE PIPE", "complainant": "Korea, 5 and 9", "respondent": "United States", "third_parties": [], "agreements": [], "articles": [], "subject": "US safeguard measure on certain imports.", "sector": "Safeguards", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• SA Arts. 3.1 and 4.2(c) (safeguard investigation – injury determination): The Appellate Body reversed the Panel's finding that the United States violated Arts. 3.1 and 4.2(c) by failing to publish in its investigation report a discrete finding or reasoned conclusion that the increased imports caused either “serious injury” or “threat of serious injury”, on the ground that the phrase “cause or threaten to cause” should be read to mean that an investigating authority has to conclude either one or both in combination as the US authority had done in the case at hand. • SA Arts. 2 and 4 (parallelism): The Appellate Body reversed the Panel's finding that Korea did not make a prima facie case of violation of the “parallelism” requirement under Arts. 2 and 4, and concluded that the United States violated the Articles since it had excluded Canada and Mexico from the application of the measure without providing adequate reasoning, while including them in the investigation. • SA Art. 4.2(b) (in", "keywords": ["safeguards"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS204", "title": "MEXICO – TELECOMS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATS Art I:2(a)", "GATS Reference Paper under", "GATS Annex on Telecommunications"], "articles": [], "subject": "Mexico's domestic laws and regulations that govern the supply of telecommunication services and federal competition laws.", "sector": "Services", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2004", "summary_ar": "", "summary_en": "• GATS Art. I:2(a) (cross border supply): The Panel found that the services at issue whereby US suppliers link their networks at the border with those of Mexican suppliers for termination within Mexico are services supplied cross-border within the meaning of Art. I:2(a), as the provision is silent as regards the place where the supplier operates, or is present, and thus is not directly relevant to the definition of “cross-border supply”. • Mexico's Reference Paper3 , Sections 2.1 and 2.2: The Panel found that (i) Mexico's commitments under Section 2 of Mexico's Reference Paper applied to the interconnection of cross-border US companies seeking to supply the services at issue into Mexico ; and (ii) Mexico was in violation of its commitments under the provision because the interconnection rates charged by Mexico's major suppliers to US suppliers were not “cost-oriented” as they were in excess of the cost rate for providing the interconnection to the US suppliers. • Mexico's Reference Pap", "keywords": ["services", "GATS", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS206", "title": "US – STEEL PLATE", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 6.8, 15 and 18.4"], "articles": [], "subject": "US imposition of anti-dumping duties on certain imports manufactured by Steel Authority of India, Ltd. (SAIL).", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 18.4 (conformity with the ADA): The Panel held that the US authority's practice in the application of “facts available” was not a measure that could be the subject of a claim. First, because such practice could be changed by the authority as long as it provided a reason for the change. Moreover, according to past WTO jurisprudence, a law can only be found inconsistent with WTO obligations if it mandates a violation. Second, the “practice” challenged by India was not within the scope of Art. 18.4, which only refers to “laws, regulations and administrative procedures”. • ADA Art. 6.8 and Annex II(3) (evidence – facts available): (as applied claim) The Panel found that the US authority acted inconsistently with the ADA in finding that SAIL had failed to provide necessary information in response to questionnaires during the course of the investigation and in consequently basing their determination entirely on “facts available”, because the information provided by SAIL met all cr", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS211", "title": "EGYPT – STEEL REBAR", "complainant": "Turkey", "respondent": "Egypt", "third_parties": [], "agreements": ["ADA Arts. 2, 3 and 6"], "articles": [], "subject": "Egypt's definitive anti-dumping measures.", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ADA Art. 3.4 (injury determination – injury factors): The Panel interpreted evaluation under Art. 3.4 to mean a process of analysis and interpretation of the facts established, in relation to each listed factor. In the light of this interpretation, the Panel concluded that Egypt acted inconsistently with Art. 3.4 in failing to evaluate six of the factors (productivity, actual and potential negative effects on cash flow, employment, wages and ability to raise capital or investments) as claimed by Turkey but was not in violation with regard to two of the factors (capacity utilization, return on investment). • ADA Art. 6.8 and Annex II(6) (evidence – facts available): The Panel found that with respect to the investigation of two exporters, Egypt was in violation of Art. 6.8 and Annex II(6), as the investigating authorities, having identified and received the requested information from those companies, nevertheless concluded that the companies had failed to provide the “necessary informa", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS212", "title": "US – COUNTERVAILING MEASURES ON CERTAIN EC PRODUCTS", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1, 14 and 21"], "articles": [], "subject": "US countervailing duty law governing the treatment of subsidies provided to state-owned companies later privatized, including certain subsidy calculation methodologies developed by the United States D", "sector": "Subsidies & Anti-Subsidy", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• ASCM Arts. 1 (definition of a subsidy) and 14 (benefit – calculation of amount of subsidy): The Appellate Body reversed the Panel in its findings and stated instead that privatizations at arm's length and at fair market value gave rise to a rebuttable presumption that a benefit ceased to exist after such privatization. It shifts the burden on the investigation authority to establish that the benefits from the previous financial contribution does indeed continue beyond such privatization. • ASCM Art. 19.1 (original investigation), Art. 21.2 (administrative review) and Art. 21.3 (sunset review): Based on its analysis above on Arts. 1 and 14, the Appellate Body upheld the Panel's finding that the “same person” methodology was as such inconsistent with Arts. 19.1, 21.2 and 21.3. Based on this methodology and without further analysis, the USDOC had concluded that a privatized enterprise continued to receive the benefits of a previous financial contribution, irrespective of the price paid ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS213", "title": "US – CARBON STEEL", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Art. 21.3"], "articles": [], "subject": "US laws, regulations, administrative procedures and policy bulletin governing “sunset” reviews of countervailing duties (CVDs), and their application in a sunset review of a CVD order on imports from ", "sector": "Metals & Mining", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 21.3 (sunset review – de minimis standard): The Appellate Body reversed the Panel's finding that the US law was in violation of Art 21.3, on the grounds that Art. 21.3 does not require the application of a 1 per cent de minimis standard in sunset reviews. The Appellate Body disagreed with the Panel's reasoning that the de minimis requirement of Art. 11.9 of the ASCM (which applies to original investigations) is implied in Art. 21.3, on the grounds that Art. 21.3 does not have an express reference to the de minimis standard nor is there a textual link (cross-reference) between the two Articles. • ASCM Art. 21.3 (sunset review – initiation by investigating authority): The Appellate Body upheld the Panel's findings that the automatic self-initiation of sunset reviews by investigating authorities under US law and accompanying regulations are consistent with the ASCM. The Appellate Body stated that its review of the context of Art. 21.3 revealed no indication that the ability of", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS219", "title": "EC – TUBE OR PIPE FITTINGS", "complainant": "Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["ADA Arts. 1, 2 and 3", "GATT Art. VI:2"], "articles": [], "subject": "EC Regulation imposing anti-dumping duties on certain imports.", "sector": "Anti-Dumping", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. VI:2 (imposition and collection of anti-dumping duties) and ADA Art. 1 (principles): The Appellate Body agreed with the Panel that there was nothing in the ADA that requires investigating authorities to reassess a determination of dumping on the basis of a devaluation occurring during the period of investigation (POI), and thus upheld the Panel's rejection of Brazil's claims. • ADA Art. 2.2.2, chapeau (dumping determination – normal value): The Panel rejected Brazil's claim that the EC authorities should have excluded low volume sales figures from their calculation of “normal value” on the ground that the chapeau only allows investigating authorities to exclude data from production and sales that were not made in the ordinary course of trade. The Appellate Body upheld the Panel's findings. • ADA Arts. 3.2 (injury determination – volume of imports) and 3.3 (injury determination – cumulative assessment of the effects of imports): The Appellate Body upheld the Panel's findings", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS231", "title": "EC – SARDINES", "complainant": "Peru", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Annex 1.1 and Art. 2.4"], "articles": [], "subject": "EC Regulation establishing common marketing standards for preserved sardines, including a specification that only products prepared from Sardina pichardus could be marketed/labelled as preserved sardi", "sector": "Standards & TBT", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2002", "summary_ar": "", "summary_en": "• TBT Agreement Annex 1.1 (technical regulation): The Appellate Body upheld the Panel's finding that the EC Regulation was a “technical regulation” within the meaning of Annex 1.1 as it fulfilled the three criteria laid down in the Appellate Body report in EC – Asbestos: (i) the document applied to an identifiable product or group of products; (ii) it lays down one or more product characteristics; and (iii) compliance with the product characteristics was mandatory. • TBT Agreement Art. 2.4 (international standard): The Appellate Body upheld the Panel's finding that the definition of “standard” does not require that a standard adopted by a “recognized body” be approved by consensus. Therefore, the standard in question, Codex Stan 94, fell within the scope of Art. 2.4 as well. • TBT Agreement Art. 2.4 (international standard – burden of proof): The Appellate Body reversed the Panel's finding that the European Communities had the burden of proving that the relevant international standard ", "keywords": ["standards & tbt", "TBT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS236", "title": "US – SOFTWOOD LUMBER III", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 14, 17 and 20"], "articles": [], "subject": "Preliminary countervailing duty determination and preliminary critical circumstances determination made by the US authorities in respect of lumber imports and US laws on expedited reviews and “adminis", "sector": "Subsidies & Anti-Subsidy", "year": 2002, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2002", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a): (1): (iii) (definition of a subsidy – financial contribution): The Panel concluded that the US authorities' determination that the Canadian provincial stumpage programme constituted a “financial contribution” by the government within the terms of Art. 1.1(a)(iii) was not inconsistent with the ASCM. The Panel considered that the Canadian government act of allowing companies to cut the trees amounted to the “supply” of standing timber, which is a good within the meaning of Art. 1.1(a)(1)(iii). • ASCM Art. 14 and 14(d) (benefit – calculation of amount of subsidy): The Panel concluded that the US authorities acted inconsistently with Art. 14 and 14(d) by using the US stumpage prices instead of the prevailing market conditions for the product at issue in Canada, the country of provision or purchase, as required by Art. 14(d), in determining whether a “benefit” accrued from the Canadian government to the recipient. • ASCM Art. 1.1(b) (definition of a subsidy – benefit): T", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS238", "title": "ARGENTINA – PRESERVED PEACHES", "complainant": "Chile, 4.1 and 4.2", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Art. XIX:1(a)"], "articles": [], "subject": "Argentina's safeguard measures imposed, in the form of specific duties, on preserved peaches from all countries other than MERCOSUR States and South Africa.", "sector": "Safeguards", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2003", "summary_ar": "", "summary_en": "• GATT Art. XIX:1(a) (unforeseen developments): The Panel noted the two distinct requirements under Art. XIX:1(a) to be fulfilled before the imposition of safeguard measures: (i) demonstration of increased imports and (ii) demonstration of unforeseen developments. The Panel concluded that on the facts of the case it was not evident that the Argentine authorities had discussed or offered any explanation on why the developments were “unforeseen” at the time of the negotiation of the obligations, and, therefore, that they had not fulfilled the criteria of Art. XIX:1(a). • SA Arts. 2.1 and 4.2(a) and GATT Art. XIX:1(a) (conditions for safeguard measures – increased imports): The Panel noted that the increase in imports must be “qualitative” as well as “quantitative”, and concluded that the Argentine authorities had failed to demonstrate that: (i) they had considered trends in imports in absolute terms, which significantly showed a decline over the period of analysis; and (ii) the increase ", "keywords": ["safeguards", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS241", "title": "ARGENTINA – POULTRY ANTI-DUMPING DUTIES", "complainant": "Brazil", "respondent": "Argentina", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 5 and 6"], "articles": [], "subject": "Definitive anti-dumping measures, in the form of specific anti-dumping duties, imposed by Argentina on imports from Brazil for a period of three years.", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• ADA Art. 5.3 (initiation of investigation – application): The Panel found that, by basing the determination of initiation of an investigation on “some” instances of dumping, Argentina violated Art. 5.3 as a dumping determination should be made in respect of the product as a whole for “all” comparable transactions, not for individual transactions. • ADA Art. 5.8 (initiation of investigation – insufficient evidence): The Panel found that Argentina violated Art. 5.8 as it failed to reject an application for investigation which was based on insufficient evidence following the issuance of a negative injury determination from the relevant investigation authority. • ADA Art. 6.8 (evidence – facts available): The Panel found that Argentina was not in violation of Art. 6.8 when it disregarded information submitted by a company that had not fulfilled procedural provisions of the domestic law. As information submitted by such companies was not considered “appropriately submitted” within the mea", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS243", "title": "US – TEXTILES RULES OF ORIGIN", "complainant": "India", "respondent": "United States", "third_parties": [], "agreements": ["ROA Art. 2"], "articles": [], "subject": "Rules of origin applied by the United States to textiles and apparel products and used in administering the textile quota regime maintained by the United States under the Agreement on Textiles and Clo", "sector": "Textiles", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• ROA Art. 2(b) (trade objectives): The Panel rejected India's claim and concluded that although the objectives of protecting the domestic industry against import competition and of favouring imports from one Member over imports from another may in principle be considered to constitute “trade objectives” for which rules of origin may not be used, India had failed to establish that US rules of origin were being administered to pursue trade objectives in violation of Art. 2(b). • ROA Art. 2(c), first sentence (restrictive, distorting or disruptive effects): The Panel rejected India's claim on the grounds that for there to be a violation of Art. 2(c), it must be proved that there is a causal link between the challenged rules of origin itself and the prohibited effects. The Panel further recognized that it would not always and necessarily be sufficient for a complaining party to show that the challenged rules of origin adversely affect one Member's trading as it may favourably affect the t", "keywords": ["textiles", "ROA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS244", "title": "US – CORROSION RESISTANT STEEL SUNSET REVIEW", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 11.3"], "articles": [], "subject": "(i) US statute for sunset review of anti-dumping duties, in conjunction with the Statement of Administrative Action (SAA), certain provisions of the US regulations related to sunset reviews and the Su", "sector": "Metals & Mining", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review • ADA Art. 11.3 (continuation of dumping and injury): The Appellate Body made some general observations with regard to such a determination: (i) the second condition of Art. 11.3 involved a prospective determination on the part of the investigating authorities, requiring a forward-looking analysis of what would be likely to occur if the duty were terminated; (ii) as to the standard of “likely”, a positive determination may be made only if the evidence demonstrated that dumping would be “probable” (not possible or plausible) if the duty were terminated; and (iii) Art. 11.3 does not prescribe any particular methodology to be used by investigating authorities in making a likelihood determination. • ADA Arts. 11.3 and 2.4 (fair comparison): The Appellate Body reversed the Panel's finding and concluded that the United States violated Art. 11.3 by relying on dumping margins calculated in previous reviews using the “zeroing” methodology. While there is no obligation under Art. 1", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS245", "title": "JAPAN – APPLES", "complainant": "United States", "respondent": "Japan", "third_parties": [], "agreements": ["SPS Arts. 2.2, 5.7 and 5.1", "DSU Art. 11"], "articles": [], "subject": "Certain Japanese measures restricting imports of apples on the basis of concerns about the risk of transmission of fire blight bacterium.", "sector": "Agriculture & Food", "year": 2003, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2003", "summary_ar": "", "summary_en": "• SPS Art. 2.2 (sufficient scientific evidence): The Appellate Body upheld the Panel's finding that the measure was maintained “without sufficient scientific evidence” inconsistently with Art. 2.2, as there was a clear disproportion (and thus no rational or objective relationship) between Japan's measure and the “negligible risk” identified on the basis of the scientific evidence. • SPS Art. 5.7 (provisional measure): The Appellate Body upheld the Panel's finding that the measure was not a provisional measure justified within the meaning of Art. 5.7, as the measure was not imposed in respect of a situation “where relevant scientific evidence is insufficient”. Having noted that the pertinent question under Art. 5.7 is whether the body of available scientific evidence does not allow, in quantitative or qualitative terms, the performance of an adequate assessment of risks as required under Art. 5.1 and as defined in Annex A of the SPS Agreement, the Appellate Body found that in light of t", "keywords": ["agriculture & food", "SPS", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS264", "title": "US – SOFTWOOD LUMBER V", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 4, 5, 6, 9 and 18"], "articles": [], "subject": "US final anti-dumping duties.", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Dumping determination • ADA Art. 2.4 and 2.4.2 (zeroing): The Appellate Body upheld the Panel's (majority) finding that the US acted inconsistently with the first sentence of Art. 2.4.2 in determining dumping margins on the basis of a methodology incorporating zeroing in the aggregation of results of comparisons of weighted average normal value with a weighted average of prices of all comparable export transactions. The Appellate Body ruled in this case only on the first methodology provided for in Art. 2.4.2, first sentence, that is weighted average normal value compared with a weighted average of export prices • ADA Art. 2.2.1.1, 2.2.2 and 2.4 (allocation of financial expenses): The Appellate Body reversed the Panel's legal interpretation under Art. 2.2.1.1 of the phrase “consider all available evidence on the proper allocation of costs” that an investigating authority is never required to “compare various cost allocation methodologies to assess their advantages and disadvantages” an", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS265", "title": "EC – EXPORT SUBSIDIES ON SUGAR", "complainant": "Australia, Thailand, Brazil, 8 and 9.1", "respondent": "European Communities", "third_parties": [], "agreements": [], "articles": [], "subject": "EC measures relating to subsidization of the sugar industry, namely, a Common Organization for Sugar (CMO) (set out in Council Regulation (EC) No. 1260/2001): two categories of production quotas – “A ", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• EC export subsidy commitment levels for sugar: The Appellate Body upheld the Panel's finding that footnote 1 in the EC Schedule relating to preferential imports from certain ACP countries and India did not have the legal effect of enlarging or otherwise modifying the European Communities' quantity commitment level contained in Section II, Part IV of its Schedule. • AA Arts. 9.1(c), 3.3 and 8 (export subsidies – exports of C sugar): The Appellate Body upheld the Panel's finding that the European Communities violated Arts. 3.3 and 8 by exporting C sugar because export subsidies in the form of payments on the export financed by virtue of government action within the meaning of Art. 9.1(c) were provided in excess of the European Communities' commitment level. In this regard, the European Communities provided two types of “payments” within the meaning of Art. 9.1(c) for C sugar producers, i.e. (i) sales of C beet below the total costs of production to C sugar producers; and (ii) transfers", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS267", "title": "US – UPLAND COTTON (ARTICLE 21.5 – BRAZIL)", "complainant": "Brazil", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts.3, 5(c), 6.3(c), and item", "DSU Arts. 11 and 21.5"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2008, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2008", "summary_ar": "", "summary_en": "• AA Arts. 10.1 and 8, and ASCM Arts 3.1(a), 3.2 and the Illustrative List of Export Subsidies, item (j): The Appellate Body upheld the Panel's finding that export credit guarantees provided under the revised GSM 102 programme were “export subsidies” because the premiums charged were inadequate to cover the long-term operating costs and losses of the programme, within the meaning of item (j) of the Illustrative List. The Appellate Body upheld the Panel's finding under item (j) despite having found that the Panel's analysis of certain quantitative evidence concerning the financial performance of the revised GSM 102 programme did not meet the requirements of DSU Art. 11. Upon finding that the Panel acted inconsistently with DSU Art. 11, the Appellate Body completed the analysis and found that the Panel's finding on the structure, design, and operation of the revised GSM 102 programme, in the light of the quantitative evidence, provided a sufficient evidentiary basis for the conclusion th", "keywords": ["subsidies & anti-subsidy", "ASCM", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS268", "title": "US – OIL COUNTRY TUBULAR GOODS SUNSET REVIEWS", "complainant": "Argentina, Annex II", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2, 3, 6,11,12, 18 and"], "articles": [], "subject": "US anti-dumping duties as well as laws, regulations and practice governing sunset reviews under the Sunset Policy Bulletin (SPB).", "sector": "Anti-Dumping", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2004", "summary_ar": "", "summary_en": "Sunset review (ADA Art. 11.3): as such violations • SPB (DSU Art. 11): The Appellate Body upheld the Panel's finding that the SPB was a “measure” subject to WTO dispute settlement; however, due to what it considered to be an insufficient analysis, it found that the Panel had failed to make an objective assessment of the matter within the meaning of DSU Art. 11 and reversed the Panel's finding that Section II.A.3 of the SPB was inconsistent, as such, with Art. 11.3. It did not complete the analysis on this issue. • “Affirmative and deemed waiver provisions”:3 The Appellate Body upheld the Panel's findings that the waiver provisions relating to waiver of participation in sunset review proceedings were, as such, inconsistent with the requirements relating to the likelihood of dumping determination under Art. 11.3 because they required assumptions about a company's likelihood of dumping. Also, having concluded that the respondents' incomplete substantive submissions should still be taken i", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS269", "title": "EC – CHICKEN CUTS", "complainant": "Thailand, Brazil", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Art. II:1"], "articles": [], "subject": "EC measures pertaining to the tariff reclassification from heading 02.10 (relating to, inter alia, salted chicken) to heading 02.07 (relating to, inter alia, frozen chicken) of certain frozen boneless", "sector": "Other", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body upheld the Panel's ultimate finding that the EC measures (relating to tariff classification) imposed duties on the products at issue in excess of the relevant heading of the EC tariff commitment because under the EC Schedule, tariffs on frozen meat (02.07) are higher than on salted meat (02.10) and, thus, violated Arts. II:1(a) and (b). Interpretation3 of the term at issue “salted” in EC Schedule • Ordinary meaning (VCLT Art. 31(1)): The Appellate Body upheld the Panel's finding that “in essence, the ordinary meaning of the term 'salted' ... indicates that the character of a product has been altered through the addition of salt” and that “there is nothing in the range of meanings comprising the ordinary meaning of the term 'salted' that indicates that chicken to which salt has been added is not covered by the concession contained in heading 02.10 of the EC Schedule”. • Context (VCLT Art. 31(2)): Having considered relevant ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS273", "title": "KOREA – COMMERCIAL VESSELS", "complainant": "European Communities, 6.3(a)", "respondent": "Korea", "third_parties": [], "agreements": ["ASCM Arts. 3.1(a),3.2, 4.7, 5(c) and"], "articles": [], "subject": "Korea's various measures relating to alleged subsidies to its shipbuilding industry.2", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "ASCM Art. 3.1(a) and 3.2 (export subsidies) • Measures as such: Having found that the KEXIM legal regime (KLR), APRG and PSL programmes did not “mandate” the conferral of a “benefit,” the Panel rejected EC claims that these measures as such were inconsistent with Art. 3.1(a) and 3.2. • Measures as applied: The Panel found that certain “KEXIM guarantees” under the APRG programme were prohibited export subsidies (specific subsidies contingent upon export performance) under Art. 3.1(a) and 3.2 and rejected Korea's argument that item (j) (i.e. export credit guarantee) of the Illustrated List could work as an affirmative defence, on the ground that item (j) does not fall within the scope of footnote 54 of ASCM. The Panel also found that certain “KEXIM loans” under the PSL programme were prohibited export subsidies and rejected Korea's defence under item (k) (export credit grants) since the PSLs (as credits to shipbuilders rather than foreign buyers) were not export credits. ASCM Part III (a", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS276", "title": "CANADA – WHEAT EXPORTS AND GRAIN IMPORTS", "complainant": "United States", "respondent": "Canada", "third_parties": [], "agreements": ["GATT Arts. XVII:1 and III:4"], "articles": [], "subject": "Canadian Wheat Board (CWB) Export Regime2 and requirements related to the import of grain into Canada.", "sector": "Agriculture & Food", "year": 2004, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2004", "summary_ar": "", "summary_en": "GATT Art. XVII:1 (State Trading Enterprise (STE)) • Relationship between paras. (a) and (b) of Art. XVII:1: The Appellate Body reasoned that subpara. (a) is the general and principal provision, and subpara. (b) explains it by identifying the types of differential treatment in commercial transactions that are most likely to occur in practice. Therefore, most, if not all, claims raised under Art. XVII:1 will require a sequential analysis of both subparas. (a) and (b). At the same time, because both subparas. (a) and (b) define the scope of that non-discrimination obligation, panels would not always be in a position to make any finding of violation of Art. XVII:1 until they have properly interpreted and applied both provisions. The Appellate Body, however, rejected Canada's contention that the Panel's approach constituted legal error. Although the Panel refrained from explicitly defining the relationship between the first two subparas. of Art. XVII:1 and proceeded on the basis of an assum", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS282", "title": "US – ANTI-DUMPING MEASURES ON OIL COUNTRY TUBULAR GOODS", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 3 and 11"], "articles": [], "subject": "Determinations by the United States Department of Commerce (USDOC) and the International Trade Commission (ITC) in the sunset review of the anti-dumping duties on Oil Country Tubular Goods (OCTG) impo", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Art 11.3 (review of anti-dumping duties): The Appellate Body reversed the Panel's finding that the Sunset Policy Bulletin (SPB) as such was inconsistent with ADA Art. 11.3 due to the Panel's failure to make “an objective assessment of the matter and the facts of the case” as required by DSU Art. 11. The Panel initially found that the SPB established an “irrebuttable presumption” of likelihood of dumping inconsistently with ADA Art. 11.3, as the USDOC treated the standard set out in SPB as conclusive or determinative as to the “likelihood” of continuation or recurrence of dumping in “sunset reviews”. • ADA Art. 11.3 (review of anti-dumping duties – likelihood of dumping): The Panel concluded that the USDOC's determination of likelihood of continuation or recurrence of dumping in the sunset review at issue was inconsistent with Art. 11.3 because it had failed to consider relevant evidence submitted by Mexican exporters and almost exclusively relied on the basis of a decline in impo", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS285", "title": "US – GAMBLING", "complainant": "Antigua and Barbuda", "respondent": "United States", "third_parties": [], "agreements": ["GATS Arts. XIV(a) and XIV(c) and XVI"], "articles": [], "subject": "Various US measures relating to gambling and betting services, including federal laws such as the “Wire Act”, the “Travel Act” and the “Illegal Gambling Business Act” (IGBA).", "sector": "Services", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• Scope of GATS commitments: The Appellate Body upheld, based on modified reasoning, the Panel's finding that the US GATS Schedule included specific commitments on gambling and betting services. Resorting to “document W/120” and the “1993 Scheduling Guidelines”3 as “supplementary means of interpretation” under Art. 32 of the VCLT, rather than context (Art. 31), the Appellate Body concluded that the entry, “other recreational services (except sporting)”, in the US Schedule must be interpreted as including “gambling and betting services” within its scope. • GATS Art. XVI:1 and 2 (market access commitment): The Appellate Body upheld the Panel's finding that the United States acted inconsistently with Art. XVI:1 and 2, as the US federal laws at issue, by prohibiting the cross-border supply of gambling and betting services where specific commitments had been undertaken, amounted to a “zero quota” that fell within the scope of, and was prohibited by, Art. XVI:2(a) and (c). However, it revers", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS294", "title": "US – ZEROING (EC)", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 9.3, 2.4 and 2.4.2", "GATT Art. VI:2"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in determining dumping margins in anti-dumping proceedings as well as the zeroing methodology as such. 2. SUMMARY OF KEY PANEL/AB FINDINGS As appl", "sector": "Anti-Dumping", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2006", "summary_ar": "", "summary_en": "As applied claims • ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that the zeroing methodology, as applied by the United States in the administrative reviews at issue, was inconsistent with ADA Art. 9.3 and GATT Art. VI:2, as it resulted in amounts of anti-dumping duties that exceeded the foreign producers’ or exporters’ margins of dumping. Under ADA Art. 9.3 and GATT Art. VI:2, investigating authorities are required to ensure that the total amount of anti-dumping duties collected on the entries of a product from a given exporter shall not exceed the margin of dumping established for that exporter. • ADA Art. 2.4, third to fifth sentences (dumping determination – due allowance or adjustment): The Appellate Body agreed with the Panel that, conceptually, zeroing is not “an allowance or adjustment” falling within the scope of Art. 2.4, third to fifth sentences, which covers allowances or adjustments that a", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS295", "title": "MEXICO – ANTI-DUMPING MEASURES ON RICE", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["ADA Arts. 3, 5.8, 6, 9, 11 12 and 17"], "articles": [], "subject": "Mexico's definitive anti-dumping duties; several provisions of Mexico's Foreign Trade Act; and the Federal Code of Civil Procedure.", "sector": "Agriculture & Food", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 3.1, 3.2, 3.4 and 3.5 (injury determination – period for the injury investigation): The Appellate Body upheld the Panel's finding that Mexico violated Arts. 3.1, 3.2, 3.4 and 3.5, as it based its determination of injury on a period of investigation which ended more than 15 months before the initiation of the investigation, and thus it had failed to make an injury determination based on positive evidence, and involving an objective examination of the volume and price effects of the alleged dumped imports or the impact of the imports on domestic producers at the time measures were imposed under Art. 3. • ADA Art. 3.1 (injury determination – use of data from part of the investigation period): The Appellate Body upheld the Panel's finding that the investigating authority's injury analysis was inconsistent with Art. 3.1 because it examined only part of the data from the investigation period and the choice of the limited period of investigation reflected the highest import penetr", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS299", "title": "EC – COUNTERVAILING MEASURES ON DRAM CHIPS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 12, 14 and 15"], "articles": [], "subject": "EC definitive countervailing duties.", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1)(iv) (definition of a subsidy – financial contribution): The Panel held that the European Communities' “financial contribution” finding with respect to one of Korea's five alleged subsidy programmes3 was inconsistent with Art. 1.1(a) (1)(iv), as it considered that the evidence before the EC investigating authority (i.e. government official's presence at Hynix's Creditor Council meeting) was insufficient for it to reasonably conclude that the Korean government entrusted or directed the private banks to purchase Hynix convertible bonds. The Panel held that the European Communities' finding on the other four programmes was consistent with Art. 1.1(a). • ASCM Arts. 1.1(b) and 14 (definition of a subsidy – benefit): The Panel found that the European Communities failed to establish the “existence” of a “benefit” from the financial contribution provided under one of the programmes (i.e. Syndicated Loan) within the meaning of Art 1.1(b), as it had ignored the loans provide", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS301", "title": "EC – COMMERCIAL VESSELS", "complainant": "Korea", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. III:4, I:1 and III:8(b)", "DSU Art. 23.1", "ASCM Art. 32"], "articles": [], "subject": "The European Communities' Temporary Defensive Mechanism for Shipbuilding (the “TDM Regulation”) of 2002, under which contract-related operating aid provided by EC member States for the building of cer", "sector": "Subsidies & Anti-Subsidy", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• GATT Arts. III:4 (national treatment – domestic laws and regulations) and III:8(b) (national treatment – subsidies exception): The Panel concluded that the state aid subject to the TDM Regulation was covered by GATT Art. III:8(b) because it provided for “the payment of subsidies exclusively to domestic producers”, and therefore the TDM Regulation, the national TDM schemes (in this case, Denmark, France, Germany, the Netherlands and Spain) and the EC decisions authorizing the schemes were not inconsistent with GATT Art. III:4. • GATT Arts. I:1 (most-favoured-nation treatment) and III:8(b) (national treatment – subsidies exception): Based on its conclusion that the TDM Regulation was covered by GATT Art. III:8(b) and that, as a result, the subsidies under the TDM Regulation were not covered by the expression “matters referred to in paras. 2 and 4 of Article III” in Art. I:1, the Panel concluded that the TDM Regulation and the national TDM schemes were not inconsistent with GATT Art. I:", "keywords": ["subsidies & anti-subsidy", "GATT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS308", "title": "MEXICO – TAXES ON SOFT DRINKS", "complainant": "United States", "respondent": "Mexico", "third_parties": [], "agreements": ["GATT Arts. III and XX(d)"], "articles": [], "subject": "Mexico's tax measures under which soft drinks using non-cane sugar sweeteners were subject to 20 per cent taxes on (i) their transfer and importation; and (ii) specific services provided for the purpo", "sector": "Agriculture & Food", "year": 2006, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2006", "summary_ar": "", "summary_en": "National treatment • GATT Arts. III:2 (national treatment – taxes and charges), first sentence (like products): As for soft drinks sweetened with HFCS, the Panel found that the tax measures were inconsistent with Art. III:2, first sentence, as these drinks were subject to internal taxes (20 per cent transfer and services taxes) in excess of taxes imposed on like domestic products – i.e. soft drinks sweetened with cane sugar (exemption from those taxes). • GATT Art. III:2 (national treatment – taxes and charges), second sentence (directly competitive or substitutable products): As for non-cane sugar sweeteners such as HFCS, the Panel found that the tax measures were inconsistent with Art. III:2, second sentence as “the dissimilar taxation (i.e. 20 per cent transfer and services taxes)” imposed on “directly competitive or substitutable imports (HFCS) and domestic products (cane sugar)” was applied in a way that afforded protection to domestic production. • GATT Art. III:4 (national treat", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS312", "title": "KOREA – CERTAIN PAPER", "complainant": "Indonesia", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 2, 3, 6, 9, 12 and Annex II"], "articles": [], "subject": "Anti-dumping duties imposed by Korea on certain imports.", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "• ADA Arts. 2,2, 6.8 and Annex II(3) (dumping determination – facts availabe): The Panel found that the Korean investigating authority (i.e. KTC) did not act inconsistently with Art. 6.8 and Annex II(3) when it resorted to facts available for the calculation of normal value for two Indonesian exporters because the information requested (financial statements and accounting records) had not been submitted “within a reasonable period of time”. In addition, the data submitted to the KTC after the deadline were not verifiable within the meaning of Annex II(3) in light of the fact that the exporters refused to submit corroborating information during the verification. The Panel also found that the KTC complied with its obligation under Annex II(6) to inform the exporters of its decision to use facts available. The Panel also found that the KTC did not act inconsistently with Art. 2.2 in basing its normal value determination on constructed value under Art. 2.2, as the data (on domestic sales) ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS322", "title": "US – ZEROING (JAPAN)", "complainant": "Japan", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2, 9 and 11", "GATT Arts. VI", "DSU Art. 11"], "articles": [], "subject": "The United States' “zeroing” procedures in the context of original investigations, periodic reviews, new shipper and changed circumstances reviews, and sunset reviews; and the application of “zeroing”", "sector": "Anti-Dumping", "year": 2005, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2005", "summary_ar": "", "summary_en": "As such claims • ADA Arts. 2.1, 2.4 and 2.4.2 and GATT Arts. VI:1 and VI:2 (zeroing in transaction-to-transaction comparisons in original investigations): The Appellate Body reversed the Panel's finding that the United States did not act inconsistently with Arts. 2.1, 2.4, and 2.4.2 by maintaining zeroing procedures in original investigations when calculating margins of dumping on the basis of transaction-to-transaction comparisons. The Appellate Body noted that because dumping and margins of dumping can only be found to exist in relation to the product under investigation, and not at the level of an individual transaction, all of the comparisons of normal value and export price must be considered. By disregarding certain comparison results, the United States acted inconsistently with Art. 2.4.2, with the “fair comparison” requirement of Art. 2.4, given that zeroing artificially inflates the magnitude of dumping. • ADA Arts. 2.1, 2.4, 9.1, 9.3 and 9.5 and GATT Arts VI:1 and VI:2 (zeroi", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS332", "title": "BRAZIL – RETREADED TYRES", "complainant": "European Communities, and (d), and XXIV", "respondent": "Brazil", "third_parties": [], "agreements": ["GATT Arts. I:1, III:4 , XI:1, XIII:1, XX(b)"], "articles": [], "subject": "(i) Brazil's import prohibition on retreaded tyres (Import Ban); (ii) fines on importing, marketing, transportation, storage, keeping or warehousing of retreaded tyres; (iii) Brazilian state law restr", "sector": "Other", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2007", "summary_ar": "", "summary_en": "• GATT Art. XI (prohibition on quantitative restrictions): The Panel concluded that Brazil's import prohibition on retreaded tyres and the fines imposed by Brazil on importation, marketing, transportation, storage, keeping or warehousing of retreaded tyres were inconsistent with Art. XI:1. • GATT Art. III:4 (national treatment – domestic laws and regulations): The Panel found that the measure maintained by the Brazilian State of Rio Grande do Sul in respect of retreaded tyres, Law 12.114, as amended by Law 12.381, was inconsistent with Art. III:4. • GATT Art. XX(b) (general exceptions – necessary to protect human life or health): The Appellate Body upheld the Panel's finding that the Import Ban was provisionally justified as “necessary” within the meaning of Art. XX(b). The Panel “weighed and balanced” the contribution of the Import Ban to its stated objective against its trade restrictiveness, taking into account the importance of the underlying interests or values. The Panel correctl", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS335", "title": "US – SHRIMP (ECUADOR)", "complainant": "Ecuador", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States' final anti-dumping measures including margins of dumping calculated using “zeroing” under the weighted-average-to weighted-average methodology.", "sector": "Agriculture & Food", "year": 2007, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2007", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel found that the United States Department of Commerce “USDOC” acted inconsistently with the first sentence of Art. 2.4.2 by using “zeroing” in calculating margins of dumping under the weighted-average-to-weighted-average methodology in the context of an original investigation.", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS339", "title": "CHINA – AUTO PARTS", "complainant": "United States, Communities, Canada", "respondent": "China", "third_parties": [], "agreements": ["GATT Arts. II, III:2, III:4, XX(d)"], "articles": [], "subject": "Three legal instruments enacted by China2 which impose a 25 per cent “charge” 3 on imported auto parts “characterized as complete motor vehicles” based on specified criteria and prescribe administrati", "sector": "Automotive", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2009", "summary_ar": "", "summary_en": "• “Ordinary customs duty” vs “internal charge”: As a preliminary “threshold” issue, the Appellate Body upheld the Panel's characterization of the charge as an “internal charge” (Art. III:2), rather than as an “ordinary customs duty” (first sentence, Art. II:1(b)), because, after considering the characteristics of the measure, the Panel had properly ascribed legal significance to, inter alia, the fact, that the obligation to pay the charge accrues internally, after auto parts enter China. • GATT Arts. III:2 (national treatment – taxes and charges) and III:4 (national treatment – domestic laws and regulations): The Appellate Body upheld the Panel's findings that the measures violated: (i) Arts. III:2 because they imposed an internal charge on imported auto parts that was not imposed on like domestic auto parts; and (ii) Art. III:4 because they accorded imported parts less favourable treatment than like domestic auto parts by, inter alia, subjecting only imported parts to additional admin", "keywords": ["automotive", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS344", "title": "US – STAINLESS STEEL (MEXICO)", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 9.3", "GATT Art. VI:2", "DSU Art. 11"], "articles": [], "subject": "US application of the so-called “zeroing methodology” in anti-dumping proceedings as well as the zeroing methodology as such.", "sector": "Metals & Mining", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2008", "summary_ar": "", "summary_en": "• ADA Art. 9.3 and GATT Art. VI:2 (imposition and collection of anti-dumping duties): Reversing the Panel, the Appellate Body found that zeroing in administrative reviews is, as such, inconsistent with GATT Art. VI:2 and ADA Art. 9.3 because it results in the levying of anti-dumping duties that exceed the exporter's or foreign producer's margin of dumping – which operates as a ceiling for the amount of anti-dumping duties that can be levied in respect of the sales made by an exporter. The Appellate Body saw no basis in GATT Arts. VI:1 and VI:2 or in ADA Arts. 2 and 9.3 for disregarding the results of comparisons where the export price exceeds the normal value when calculating the margin of dumping for an exporter or foreign producer. Based on the same reasoning, the Appellate Body also found that the United States acted inconsistently with its obligations under GATT Art. VI:2 and ADA Art. 9.3 by using simple zeroing in five specific administrative reviews. • Status of Appellate Body re", "keywords": ["metals & mining", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS350", "title": "US – CONTINUED ZEROING", "complainant": "European Communities", "respondent": "United States", "third_parties": [], "agreements": ["DSU Arts. 6.2 and 11", "ADA Arts. 2.4.2, 9.3, 11.3 and", "GATT Art. VI:2"], "articles": [], "subject": "The European Communities challenged as a measure the ongoing application by the United States of antidumping duties resulting from anti-dumping orders in 18 specific cases, as calculated with the use ", "sector": "Anti-Dumping", "year": 2009, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2009", "summary_ar": "", "summary_en": "• ADA Art. 9.3, GATT Art. VI:2 and ADA Art. 11.3 (ongoing application of anti-dumping duties calculated with zeroing): The Appellate Body reversed the Panel's finding that the European Communities failed in its request for panel establishment to identify the measure in 18 anti-dumping cases. The Appellate Body found that the panel request identified the specific measures at issue as the continued application of anti-dumping duties calculated with the use of the zeroing methodology in each of the 18 cases listed in the annex to the panel request. The Appellate Body considered these measures to be neither rules nor norms of general application, nor specific instances of application of the zeroing methodology. Rather, they constituted ongoing conduct, which the European Communities was not precluded from challenging in WTO dispute settlement. With respect to four of the 18 cases, the Appellate Body completed the analysis and found that the continued application of anti-dumping duties was ", "keywords": ["anti-dumping", "DSU", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS360", "title": "INDIA – ADDITIONAL IMPORT DUTIES", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["GATT Arts. II:1(b) and II.2(a)"], "articles": [], "subject": "Two border charges, consisting of the “Additional Duty” imposed by India on imports of alcoholic beverages (beer, wine, and distilled spirits); and the “Extra-Additional Duty” imposed by India on impo", "sector": "Other", "year": 2008, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2008", "summary_ar": "", "summary_en": "• GATT Arts. II:1(b) and II:2(a) (schedules of concessions): The Appellate Body reversed the Panel's finding that the United States had failed to establish that the Additional Duty and the Extra-Additional Duty were inconsistent with Arts. II:1(b) and II:2(a). The Appellate Body explained that it did not see a textual or other basis for the Panel's conclusion that “inherent discrimination” is a relevant or necessary feature of charges covered by Art. II:1(b). The Appellate Body further found that the Panel erred in its interpretation of the two elements of Art. II:2(a), that is “equivalence” and “consistency with Art. III:2”. In particular, the Appellate Body disagreed with the Panel's conclusion that the term “equivalent” does not require any quantitative comparison of the charge and internal tax. Instead, the Appellate Body considered that the term “equivalent” calls for a comparative assessment that is both qualitative and quantitative in nature. Moreover, the Appellate Body clarifi", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS375", "title": "EC – IT PRODUCTS", "complainant": "United States, Japan, Chinese Taipei, Taipei", "respondent": "European Communities", "third_parties": [], "agreements": ["GATT Arts. II:1(a), II:1(b), X:1 and X:2"], "articles": [], "subject": "Various EC measures pertaining to the tariff classification, and consequent tariff treatment, of certain information technology products (IT products).", "sector": "Other", "year": 2010, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2010", "summary_ar": "", "summary_en": "• The Ministerial Declaration on Trade in Information Technology Products (ITA): The European Communities had committed in its WTO Schedule to provide duty‑free treatment to certain IT products pursuant to the ITA. The products receiving duty-free treatment were indicated in the ITA in two ways: as HS1996 headings and in “narrative description” form. • GATT Arts. II:1(a) and II:1(b) (schedules of concessions – FPDs): The Panel found that the measures at issue were inconsistent with Arts. II:1(a) and II:1(b) because they required EC member States to classify some FPDs under dutiable headings although such products fell within the scope of the “narrative description” and/or within the scope of the CN code 8471 60 90 (which pertains to “input or output units” of “automatic data-processing machines” (ADP)), both of which were duty-free in the EC Schedule pursuant to the European Communities' implementation of the ITA.3 • GATT Arts. II:1(a) and II:1(b) (schedules of concessions – STBCs): Th", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS381", "title": "US – TUNA II (MEXICO)", "complainant": "Mexico", "respondent": "United States", "third_parties": [], "agreements": ["TBT Annex 1.1, Arts. 2.1, 2.2 and 2.4", "DSU Art. 11", "GATT Arts. I:1 and III:4"], "articles": [], "subject": "(1) United States Code, Title 16, Section 1385 – “Dolphin Protection Consumer Information Act” (DPCIA); (2) Code of Federal Regulations, Title 50, Section 216.91 “Dolphin-safe labelling standards” and", "sector": "Standards & TBT", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (definition of technical regulation): The Appellate Body found that “the US measure establishes a single and legally mandated set of requirements for making any statement with respect to the broad subject of ‘dolphin-safety’ of tuna products in the United States”. Thus, it upheld the Panel’s ruling characterizing the measure at issue as a “technical regulation” within the meaning of TBT Annex 1. • TBT Art. 2.1 (national treatment – technical regulations): According to the Appellate Body, the measure at issue modified the competitive conditions in the US market to the detriment of Mexican tuna products and the United States did not demonstrate that this stemmed solely from “legitimate regulatory distinctions”. The Appellate Body, therefore found that the US “’dolphin-safe” labelling measure was inconsistent with Art. 2.1 and reversed the Panel’s contrary finding. • TBT Art. 2.2 (not more trade-restrictive than necessary): The Appellate Body disagreed with the Panel’s rul", "keywords": ["standards & tbt", "TBT", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS382", "title": "US – ORANGE JUICE (BRAZIL)", "complainant": "Brazil", "respondent": "United States", "third_parties": [], "agreements": ["ADA. Art 2.4"], "articles": [], "subject": "United States Department of Commerce's (USDOC) (i) use of zeroing in two administrative reviews and (ii) “continued use” of zeroing in successive anti-dumping proceedings.", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (dumping determination – fair comparison): The Panel concluded that the use of zeroing to determine margins of dumping and importer-specific assessment rates was inconsistent with Art. 2.4 because it involves a comparison between export price and normal value that will invariably result in a higher margin of dumping than would otherwise be the case. In reaching this conclusion, the Panel clarified that, for systemic reasons, it followed the Appellate Body's previous findings on the United States' use of zeroing in anti-dumping proceedings. The Panel found that the United States had used “zeroing” to calculate the margins of dumping and the importer-specific rates of the two Brazilian respondents investigation in the First and Second Administrative Review and thus acted inconsistently with Art. 2.4. • ADA Art. 2.4 (dumping determination – continued use of zeroing): Brazil challenged the alleged continued use by the United States of zeroing in successive anti-dumping proce", "keywords": ["anti-dumping", "ADA."], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS384", "title": "US – COOL (ARTICLE 21.5 – CANADA AND MEXICO)", "complainant": "Canada, Mexico", "respondent": "United States", "third_parties": [], "agreements": ["TBT Arts. 2.1 and 2.2,", "GATT Arts. III:4, IX, XX, and XXIII:1(b)"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2015, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2015", "summary_ar": "", "summary_en": "• TBT Art. 2.1 (less favourable treatment and detrimental impact): The Appellate Body found that the Panel did not err in its consideration of (a) the increased recordkeeping burden entailed by the amended COOL measure; and (b) the potential for label inaccuracy under the amended COOL measure, as being within its analysis of whether the detrimental impact of that measure on imported livestock stemmed exclusively from legitimate regulatory distinctions. The Panel considered that the exemptions prescribed by the amended COOL measure supported a conclusion that the detrimental impact of that measure on imported livestock did not stem exclusively from legitimate regulatory distinctions. The Appellate Body upheld this finding. As regards, the cross appeals of Canada and Mexico, the Appellate Body found that the Panel did not err by considering the amended COOL measure's prohibition of a trace-back system as not relevant for the analysis of whether the detrimental impact of that measure on i", "keywords": ["anti-dumping", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS396", "title": "PHILIPPINES – DISTILLED SPIRITS", "complainant": "European Union, United States", "respondent": "Philippines", "third_parties": [], "agreements": ["GATT Art. III:2, first and"], "articles": [], "subject": "Philippines excise tax on distilled spirits, which imposed different tax rates depending on the raw material used to make the spirit.", "sector": "Other", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• GATT Art. III:2 (national treatment – taxes and charges), first sentence (like products): The Appellate Body upheld the Panel’s finding that each type of imported distilled spirit at issue in this dispute – gin, brandy, vodka, whisky, and tequila – made from non-designated raw materials was “like” the same type of domestic distilled spirit made from designated raw materials, within the meaning of Art. III:2, first sentence. Accordingly, the Appellate Body upheld the Panel’s finding that, through its excise tax, the Philippines subjected specific types of imported distilled spirits to internal taxes in excess of those applied to like domestic spirits of the same type made from designated raw materials in violation of Art. III:2, first sentence. The Appellate Body, however, reversed the Panel’s additional finding that all distilled spirits at issue in the dispute, irrespective of their raw material base and their origin or type (brandy, whisky, rum, gin, vodka, tequila, and tequila-fla", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS399", "title": "US – TYRES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": [], "articles": [], "subject": "US transitional product-specific safeguard measure applied under para. 16 of China's Accession Protocol pursuant to Section 421 of the US Trade Act of 1974.", "sector": "Safeguards", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Safeguards السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• China's Accession Protocol, para. 16.4 (imports “increasing rapidly”): The Appellate Body upheld the Panel's finding that the United States International Trade Commission (USITC) properly established that imports of subject tyres from China met the “increasingly rapidly” threshold provided in para. 16.4. The Appellate Body reasoned that such increases in imports must be occurring over a short and recent period of time, and must be of a sufficient magnitude in relative or absolute terms so as to be a significant cause of material injury to the domestic industry. • China's Accession Protocol, para. 16.4 (causation): The Appellate Body upheld the Panel's finding that the USITC properly demonstrated that subject imports were a “significant cause” of material injury. The Appellate Body found that the causal link expressed by the term “a significant cause” in para. 16.4 requires that rapidly increasing imports make an “important” or “notable” contribution in bringing about material injury ", "keywords": ["safeguards"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS400", "title": "EC – SEAL PRODUCTS", "complainant": "Canada, Norway", "respondent": "European Communities", "third_parties": [], "agreements": ["TBT Arts. 2.1, 2.2, 5.1.2, and 5.2.1", "GATT Arts. I:1, III:4, XI:I, XX(a) and"], "articles": [], "subject": "Regulations of the European Union (EU Seal Regime) generally prohibiting the importation and placing on the market of seal products, with certain exceptions, including for seal products derived from h", "sector": "Standards & TBT", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2014", "summary_ar": "", "summary_en": "• TBT Annex 1.1 (technical regulation): The Appellate Body reversed the Panel’s intermediate finding that the EU Seal Regime lays down “product characteristics”, and consequently reversed the Panel’s finding that the EU Seal Regime was a “technical regulation” within the meaning of TBT Annex 1.1. The Appellate Body was unable to complete the legal analysis and thus did not rule on whether the EU Seal Regime lays down “related processes and production methods” within the meaning of TBT Annex 1.1. The Appellate Body therefore declared moot and of no legal effect the Panel’s conclusions under TBT Arts. 2.1, 2.2, 5.1.2, and 5.2.1. • GATT Art. I:1 (most-favoured-nation treatment): The Appellate Body upheld the Panel’s finding that the legal standard for the non-discrimination obligations under TBT Art. 2.1 does not apply equally to claims under GATT Art. I:1. The Appellate Body therefore upheld the Panel's finding that the EU Seal Regime was inconsistent with GATT Art. I:1 in respect of the", "keywords": ["standards & tbt", "TBT", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS402", "title": "US – ZEROING (KOREA)", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "Certain United States final determinations and anti-dumping duty orders that included margins of dumping calculated using “zeroing” in the context of the “weighted-average to weighted-average” methodo", "sector": "Anti-Dumping", "year": 2011, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2011", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – fair comparison): The Panel found that the United States acted inconsistently with the first sentence of Art. 2.4.2 by using the zeroing methodology in calculating certain margins of dumping in the context of the three original investigations at issue.", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS405", "title": "EU – FOOTWEAR (CHINA)", "complainant": "China", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.2, 6.5, 6.10, 9.2 and", "GATT Art. I"], "articles": [], "subject": "(1) Art. 9.5 of the European Union’s basic anti-dumping regulation (Basic AD Regulation), regulating dumped imports from non-market economies (NMEs); (2) the European Union “Definitive Regulation” imp", "sector": "Anti-Dumping", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2012", "summary_ar": "", "summary_en": "Claims related to the treatment of NMEs • ADA Arts. 6.10, 9.2, 18.4 and WTO Agreement Art. XVI:4 (individual treatment in imposing anti-dumping duties): ADA Arts. 6.10 and 9.2 support the same basic principle that individual exporters and producers in anti-dumping investigations should be treated individually in the determination and imposition of anti-dumping duties, except where it would be impracticable to do so. The Panel thus found that Art. 9.5 of the Basic AD Regulation was as such and as applied inconsistent with both of these provisions because, for NMEs, it imposed duties for producers/exporters on a country-wide basis and conditioned the calculation of individual duties on the satisfaction of individual treatment conditions. The Panel then concluded that Art. 9.5 of the Basic AD Regulation also violated WTO Agreement Art. XVI: 4 and ADA Art.18.4. • GATT Art. I:1 (most-favoured-nation treatment – treatment of NMEs): The Panel found Art. 9.5 of the Basic AD Regulation as such ", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS413", "title": "CHINA – ELECTRONIC PAYMENT SERVICES", "complainant": "United States", "respondent": "China", "third_parties": [], "agreements": ["GATS Arts. XVI and XVII"], "articles": [], "subject": "", "sector": "Services", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• Classification of the services at issue: The Panel found that electronic payment services for payment card transactions are classifiable under Subsector 7.B(d) of China’s Services Schedule, which reads “[a]ll payment and money transmission services, including credit, charge, and debit cards, travellers cheques and bankers drafts (including import and export settlement)”. It observed that the use of the term “all” manifests an intention to cover the entire spectrum of the “payment and money transmission services” encompassed under Subsector (d). • Scope of China’s GATS commitments: The Panel rejected the United States’ view that China’s Schedule includes a crossborder (mode 1) market access commitment to allow the supply of EPS into China by foreign EPS suppliers. The Panel found, however, that China’s Schedule includes a market access commitment that allows foreign EPS suppliers to supply their services through commercial presence (mode 3) in China, so long as a supplier meets certai", "keywords": ["services", "GATS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS422", "title": "US – SHRIMP AND SAWBLADES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["ADA Art. 2.4.2"], "articles": [], "subject": "United States anti-dumping measures covering two products from China.", "sector": "Agriculture & Food", "year": 2012, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2012", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping determination – zeroing): The Panel upheld China’s claim that the use of zeroing in calculating the margins of dumping in the anti-dumping investigations at issue was inconsistent with Art. 2.4.2, and therefore concluded that the United States had acted inconsistently with its obligations under this provision. ADA Art. 2.4.2 (dumping determination – separate rate calculation): The Panel rejected China’s claim concerning the separate rate in the shrimp investigation. As the investigation concerned imports from a non-market economy, the United States Department of Commerce (USDOC) assigned a “separate rate” to exporters that were able to demonstrate the absence of government control, both de jure and de facto, over their export activities; other exporters were assigned the rate for the People’s Republic of China-entity. In calculating the separate rate, the USDOC had averaged the dumping margins of the investigated companies, which were calculated with zeroing. ", "keywords": ["agriculture & food", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS425", "title": "CHINA – X-RAY EQUIPMENT", "complainant": "European Union, 6.9 and 12.2.2", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4, 3.5, 6.5.1,"], "articles": [], "subject": "Anti-dumping duties imposed by China’s Ministry of Commerce (MOFCOM) by Notice No. 1 (2011), including its Annex, on x-ray equipment from the European Union.", "sector": "Anti-Dumping", "year": 2013, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2013", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 (injury determination) and 3.2 (injury determination – volume of imports): The Panel held that MOFCOM’s price undercutting and price suppression analyses were inconsistent with Arts. 3.1 and 3.2. The Panel found that the price effects analysis were not based on an objective examination of positive evidence, as MOFCOM had failed to ensure that the prices it was comparing as part of its price effects analysis were comparable. • ADA Arts. 3.1 (injury determination) and 3.4 ((injury determination – injury factors): The Panel found MOFCOM acted inconsistently with Arts. 3.1 and 3.4 because of its failure to consider all relevant economic factors, in particular, the “magnitude of the margin of dumping” when making a determination on the state of the domestic industry. Moreover, MOFCOM’s examination was found to lack objectivity, and not to be reasoned and adequate. The Panel rejected the European Union’s claim that MOFCOM did not rely upon positive evidence in making its dete", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS436", "title": "US – CARBON STEEL (INDIA)", "complainant": "India, 14(d)", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1(a)(1), 2.1, 12.7,"], "articles": [], "subject": "Imposition by the United States of countervailing duties on imports of certain hot-rolled carbon steel flat products from India.", "sector": "Metals & Mining", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2014", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Appellate Body reversed the Panel’s finding rejecting India’s claim that the United States Department of Commerce (USDOC) determination that the National Mineral Development Corporation (NMDC) was a public body was inconsistent with ASCM Art. 1.1(a)(1). The Appellate Body considered that the Panel had correctly articulated the appropriate standard but had erred in its substantive interpretation of ASCM Art. 1.1(a)(1) by construing the term “public body” to mean any entity that is “meaningfully controlled” by a government. Consequently, the Panel had erred in its application of ASCM Art. 1.1(a)(1) to the USDOC’s public body determination, in effect treating the Government of India’s (GOI) ability to control the NMDC as determinative for purposes of establishing whether the NMDC constituted a public body. The Panel had also failed properly to consider whether the USDOC had adequately explained and supported, in its written determin", "keywords": ["metals & mining", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS437", "title": "US – COUNTERVAILING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Art. VI", "SCM Arts. 1.1, 1.1(a)(1), 1.1(b),", "DSU Arts. 6.2 and 11"], "articles": [], "subject": "Countervailing measures imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2015", "summary_ar": "", "summary_en": "• ASCM Art. 1.1(a)(1) (definition of “public body”): The Panel found that the United States Department of Commerce (USDOC) acted inconsistently with Art. 1.1(a)(1), because it determined that certain Chinese state-owned enterprises were “public bodies” based solely on the grounds that they were majority owned, or otherwise controlled, by the Government of China. The Panel also found USDOC's “rebuttable presumption” to determine whether a state-owned enterprise is a “public body” to be inconsistent as such with Art. 1.1(a)(1). • ASCM Arts. 1.1(b) and 14(d) (benefit benchmark): The Panel found that the USDOC did not act inconsistently with Arts. 14(d) or 1.1(b) by rejecting in-country private prices in China as benchmarks in its benefit analysis. Noting that the selection of a benchmark under Art. 14(d) could not, at the outset, exclude consideration of in‑country prices from any particular source, including government‑related prices, the Appellate Body reversed the Panel's finding, and ", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS438", "title": "ARGENTINA – IMPORT MEASURES", "complainant": "European Union, United States, Japan", "respondent": "Argentina", "third_parties": [], "agreements": ["GATT Arts. III:4 and XI:1"], "articles": [], "subject": "", "sector": "Other", "year": 2015, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2015", "summary_ar": "", "summary_en": "• The Appellate Body upheld the Panel's finding that the Argentine authorities' imposition on economic operators of one or more five trade-related requirements (TRRs), as a condition to import or to obtain certain benefits, operated as a single measure attributable to Argentina (a TRRs measure). • DSU Art. 6.2 (requirements of panel request): The Appellate Body reversed the Panel's finding that 23 specific instances of application of the TRRs were not properly identified in the European Union's panel request as measures at issue and were not within the Panel's terms of reference. However, the Appellate Body found it unnecessary to complete the analysis with respect to those 23 specific instances of application of the TRRs, because the conditions on which the European Union based its appeal were not met. • GATT Art. XI (prohibition on quantitative restrictions): The Appellate Body upheld the Panel's finding that the TRRs measure was a restriction on the importation of goods, inconsisten", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS442", "title": "EU – FATTY ALCOHOLS (INDONESIA)", "complainant": "Indonesia", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 1, 2.3, 2.4, 2.6, 3.1, 3.2, 3.3, 3.4,", "GATT 1994 Arts. VI and X:3(a)", "DSU Arts. 3, 10.1, 11, 12.1, 12.7, 12.12, 17.4,"], "articles": [], "subject": "Anti-dumping duties imposed by the European Union on imports of fatty alcohols from Indonesia, and aspects of the underlying anti-dumping investigation.", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Art. 2.4 (fair comparison): The EU authorities made a downward adjustment to the export price of an Indonesian producer (PT Musim Mas) for payment made by PT Musim Mas to a related trading company based in Singapore (ICOF‑S). Indonesia claimed that PT Musim Mas and ICOF‑S formed a “single economic entity” and therefore, the payment (mark-up) was not a difference affecting price comparability within the meaning of Art. 2.4. The Appellate Body observed that the focus of Art. 2.4 is not merely on a comparison between the normal value and the export price, but predominantly on the means to ensure the fairness of that comparison. Pursuant to Art. 2.4, investigating authorities are required to make due allowance for differences affecting price comparability. There are no differences affecting price comparability that are precluded, as such, from being the object of an allowance. Instead, the need to make due allowances must be assessed in light of the specific circumstances of each cas", "keywords": ["anti-dumping", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS449", "title": "US – COUNTERVAILING AND ANTI-DUMPING MEASURES (CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. X:1; X:2; X:3(b)", "SCM Arts. 10; 19.3; 32.1", "DSU Art. 6.2"], "articles": [], "subject": "", "sector": "Subsidies & Anti-Subsidy", "year": 2014, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2014", "summary_ar": "", "summary_en": "• GATT Art. X:1 (trade regulations – prompt publication): In a finding not appealed, the Panel found that Section 1 of PL112‑99 was published promptly after it had been made effective because it was published on the same date that it was made effective, and thus the United States did not act inconsistently with Art. X:1 in respect of Section 1. • GATT Art. X:2 (trade regulations – no enforcement before publication): The Appellate Body reversed the Panel's finding that, although Section 1 of PL 112‑99 is a measure of general application that has been “enforced” prior to its official publication, it fell outside the scope of Art. X:2 because it neither effects an “advance” in a rate of duty on imports under an established or uniform practice, nor imposes a “new” or “more burdensome” requirement or restriction on imports. The Appellate Body considered that, to determine whether a measure of general application increases a rate of duty or imposes a new or more burdensome requirement, the b", "keywords": ["subsidies & anti-subsidy", "GATT", "SCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS461", "title": "COLOMBIA – TEXTILES", "complainant": "Panama", "respondent": "Colombia", "third_parties": [], "agreements": ["GATT Arts. II:1, II:1(b), VIII:1, X:3(a)"], "articles": [], "subject": "A compound tariff imposed by Colombia through Presidential Decree No. 074/2013, on imports of textiles, apparel and footwear, consisting of (i) a 10 per cent ad-valorem component; and (ii) a specific ", "sector": "Textiles", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Appellate Body reversed the Panel's finding that it was unnecessary for the Panel to rule on whether Art. II:1 applies to “illicit trade”. The Appellate Body considered that the basis upon which the Panel had refrained from interpreting Art. II:1 was flawed. According to the Appellate Body, the Panel's statement implied that the measure at issue applied, or could apply, to some transactions considered by Colombia to be illicit trade, and thus the Panel was required to address the interpretative issue before it. The Appellate Body therefore found that the Panel acted inconsistently with the obligation in DSU Art. 11 to make an objective assessment of the matter, including an objective assessment of the applicability of the relevant covered agreements. In completing the legal analysis, the Appellate Body ruled that the scope of Art. II:1(a) and (b) did not exclude what Colombia classified as “illicit trade” from the requirements to respect", "keywords": ["textiles", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS464", "title": "US – WASHING MACHINES", "complainant": "Korea", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 2.4.2, 2.4, 9.3", "GATT Arts. VI:2, VI:3", "ASCM Arts. 2.2, 19.4"], "articles": [], "subject": "Definitive anti-dumping and countervailing duties applied by the US Department of Commerce (USDOC).", "sector": "Subsidies & Anti-Subsidy", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2, second sentence (pattern): The Appellate Body considered that a “pattern” comprises all export prices to a purchaser (or region or time period) which differ significantly from the export prices to other purchasers (or regions or time periods) because they are significantly lower than those other prices. The Appellate Body also found that the requirement to identify prices which differ significantly means that the authority is required to assess the price differences in a quantitative and qualitative manner. The Appellate Body thus reversed the Panel's findings to the extent it found that a pattern of export prices which differ significantly can be established “on the basis of purely quantitative criteria”. The Appellate Body held that an investigating authority must also explain why both the weighted average‑to‑weighted average (W-W) and the transaction‑to‑transaction methodologies (T-T) cannot take into account appropriately the identified differences in export price", "keywords": ["subsidies & anti-subsidy", "ADA", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS473", "title": "EU – BIODIESEL (ARGENTINA)", "complainant": "Argentina, 2.4, 3.1, 3.4, 3.5, 9.3, 18.4, Establishment of Panel, 25 April 2014, Circulation of Panel Report, 29 March 2016, WTO Agreement Art. XVI:4, Circulation of AB Report, 6 October 2016, Adoption, 26 October 2016", "respondent": "European Union", "third_parties": [], "agreements": ["ADA Arts. 2.1, 2.2, 2.2.1.1, 2.2.2 (iii),", "DSU Art. 11", "GATT Arts. VI:1, VI:1(b)(ii), VI:2"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2016", "summary_ar": "", "summary_en": "• ADA Arts. 2.2.1.1 and 2.2 / GATT Art. VI:1(b)(ii) / DSU Art. 11 (as such claims): The Appellate Body upheld the Panel’s finding that Argentina had not established that the second subparagraph of Art. 2(5) of the Basic Regulation was inconsistent as such with Arts. 2.2.1.1, 2.2 and VI:1(b)(ii). • ADA Art. 2.2.1.1 (dumping determination – cost of production on the basis of records kept): The Appellate Body considered that the second condition in the first sentence of Art. 2.2.1.1 concerns whether the records kept by the investigated exporter/producer suitably and sufficiently correspond to or reproduce those costs incurred by the exporter/producer that have a genuine relationship with the production and sale of the product under consideration. Consequently, it upheld the Panel’s finding that the European Union acted inconsistently with this provision by failing to calculate the cost of production of the product under investigation on the basis of the records kept by the producers. • AD", "keywords": ["anti-dumping", "ADA", "DSU"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS475", "title": "RUSSIA – PIGS (EU)", "complainant": "European Union, 5.2, 5.3, 5.6, 5.7, 6.1, 6.2, 6.3 and 8", "respondent": "Russia", "third_parties": [], "agreements": ["SPS Arts. 1, 2.2, 2.3, 3.1, 3.2, 5.1,"], "articles": [], "subject": "", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2017", "summary_ar": "", "summary_en": "• SPS Art. 3 (harmonization): The Panel found that the EU member State bans violated Art. 3.2 because they did not conform to the relevant OIE international standards. It found that the EU-wide ban and EU member State bans, except that in respect of Latvia, were inconsistent with Art. 3.1 because they were not based on the same standards. • SPS Arts. 5.1, 5.2, 5.3 and 2.2 (risk assessment): The Panel found that (i) the measures were not provisional measures under Art. 5.7, (ii) they violated Arts. 5.1 and 5.2 because they were not based on a risk assessment within the meaning of the Agreement, and (iii) without such a risk assessment, Russia could not have taken into account “relevant economic factors” as required by Art. 5.3. It found that Russia failed to rebut the presumption of inconsistency with Art. 2.2 raised by the violation of Arts. 5.1, 5.2 and 5.3. • SPS Art. 6 (adaptation to regional conditions): The Appellate Body upheld the Panel’s conclusion that the ban on imports from ", "keywords": ["agriculture & food", "SPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS479", "title": "RUSSIA – COMMERCIAL VEHICLES", "complainant": "European Union, 6.5, 6.5.1, 6.9, 18.4; GATT Art. VI", "respondent": "Russia", "third_parties": [], "agreements": ["ADA Arts. 1, 3.1, 3.2, 3.4, 3.5, 4.1,"], "articles": [], "subject": "The Russian Federation’s imposition of anti-dumping duties on certain light commercial vehicles from Germany and Italy pursuant to a Decision of the Board of the Eurasian Economic Commission (EEC), in", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 4.1 (definition of domestic industry): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 4.1 by not including GAZ, a domestic producer of the like product, in its definition of “domestic industry” solely on the basis that it had furnished allegedly deficient data. • ADA Arts. 3.1 and 3.2 (price suppression): The Appellate Body upheld the Panel’s finding that the DIMD acted inconsistently with Arts. 3.1 and 3.2 by failing to take into account the impact of the financial crisis in determining the rate of return used to construct the target domestic price for its price suppression analysis. However, the Appellate Body reversed the Panel’s finding that the evidence on the investigation record did not require the DIMD to examine whether the market could absorb further price increases. • DSU Art. 11 and ADA Art. 17.6 (confidential report): The Appellate Body reversed the Panel’s findings concerning three injury factors und", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS483", "title": "CHINA – CELLULOSE PULP", "complainant": "Canada", "respondent": "China", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.2, 3.4 and 3.5"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ADA Arts. 3.1 and 3.2 (injury determination – volume of dumped imports): The Panel found that China did not act inconsistently with Arts. 3.1 and 3.2 in not assessing the significance of an absolute increase in dumped imports in light of the factual circumstances in the market such as domestic demand, volume of domestic like product and non-dumped imports. The Panel highlighted the separate nature of the inquiries set out in Art. 3.2 and considered that while the principle in Art. 3.1 that an injury determination must be based on an objective examination of positive evidence applies generally to the consideration of increased imports under Art. 3.2, it does not inform the substance of that consideration. The Panel also found China’s consideration of the price effects was inconsistent with Arts. 3.1 and 3.2 of the Anti-Dumping Agreement because MOFCOM (i) failed to explain the role of those parallel price trends between dumped import and domestic like product prices in the decline of ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS485", "title": "RUSSIA – TARIFF TREATMENT", "complainant": "European Union", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Arts. II:1(a) and II:1(b)"], "articles": [], "subject": "", "sector": "Other", "year": 2016, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2016", "summary_ar": "", "summary_en": "• GATT Art. II:1(b) (schedules of concessions): The Panel found that a measure can be found to be inconsistent with Art. II:1(b), first sentence, on the basis of its design and structure, and that it is not necessary to provide evidence of actual transactions or adverse trade effects. The Panel also found that Art. II:1(b), first sentence, prohibits Members from exceeding their tariff bindings by even de minimis amounts. Finally, the Panel confirmed that Members cannot balance less favourable tariff treatment of some imports against more favourable treatment of others. Thus, a Member may not impose customs duties in excess of bound rates for some imports even if it imposes customs duties below bound rates for others. The Panel found that the first to sixth measures at issue were inconsistent with Art. II:1(b), first sentence, because they resulted in the imposition of customs duties in excess of Russia's bound rates. The Panel also found that the seventh to eleventh measures were incon", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS487", "title": "US – TAX INCENTIVES", "complainant": "European Union, 3.2", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1(a)(1)(ii), 1.1(b), 3.1(b),"], "articles": [], "subject": "Legislation enacted in the state of Washington in the United States that amended and extended tax incentives for the aerospace industry.", "sector": "Subsidies & Anti-Subsidy", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2017", "summary_ar": "", "summary_en": "• ASCM Art. 1 (definition of a subsidy): The Panel found that the tax rate, credit or exemption at issue for each of the challenged measures constituted a financial contribution under Art. 1.1(a)(1)(ii) because (i) government revenue that is otherwise due is foregone or not collected, and (ii) a benefit within the meaning of Art. 1.1(b) is thereby conferred. It thus concluded that each of the measures constituted a subsidy under Art. 1. • ASCM Art. 3 (prohibited subsidies – import substitution subsidies): The Appellate Body upheld the Panel’s finding that the siting provisions challenged by the European Union, considered either individually or together, did not violate Art. 3.1 because the European Union did not demonstrate that these measures, on their own, and based on their express terms, made the challenged aerospace tax measures de jure contingent upon the use of domestic over imported goods. The Appellate Body reversed the Panel’s finding that one of the challenged measures (the ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS492", "title": "EU – POULTRY MEAT (CHINA)", "complainant": "China, XXVIII:1, XXVIII:2", "respondent": "European Union", "third_parties": [], "agreements": ["GATT Arts. I:1, II:1, XIII:1, XIII:2, XIII:4"], "articles": [], "subject": "The modification by the European Union of tariff concessions on certain poultry products pursuant to negotiations held under GATT Art. XXVIII, and certain instruments implementing such modifications a", "sector": "Agriculture & Food", "year": 2017, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2017", "summary_ar": "", "summary_en": "• GATT Art. XXVIII (modification of schedules): The Panel found that the European Union had not acted inconsistently with Art. XXVIII:1 by not recognizing China as a Member holding a principal or substantial supplying interest in the concessions at issue because (i) it was not obliged to take into account the SPS measures that restricted Chinese poultry imports over the relevant reference periods since they were not “discriminatory quantitative restrictions”; and (ii) it was not obliged to re-determine which Members held a substantial supplying interest based on changes in import shares after the initiation of the negotiations. The Panel found that the European Union had not acted inconsistently with Art. XXVIII:2 regarding the total amount of the TRQs, because (i) it was not obliged to calculate such amount based either on an estimate of import levels in the absence of the SPS measures, or of import levels over the three years preceding the conclusion of the negotiations; and (ii) Art", "keywords": ["agriculture & food", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS511", "title": "CHINA – AGRICULTURAL PRODUCERS", "complainant": "United States, 6.3 and 7.2", "respondent": "China", "third_parties": [], "agreements": [], "articles": [], "subject": "China’s provision for domestic support, in the form of market price support, in excess of its product specific de minimis level, provided to agricultural producers of various products in 2012, 2013, 2", "sector": "Agriculture & Food", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2019", "summary_ar": "", "summary_en": "• AA Arts. 3.2 and 6.3 (domestic support commitments): The Panel found that China provided domestic support, in terms of its Current Total Aggregate Measurement(s) of Support (AMS), in the form of market price support to the producers of certain agricultural products in excess of its commitment level of “nil”, set forth in Section I of Part IV of China’s Schedule of Concessions on Goods CLII, in violation of Arts. 3.2 and 6.3. • AA Art. 7.2(b) (prohibition of domestic support to agricultural producers in excess of the relevant de minimis level): Having found that China had acted inconsistently with Arts. 3.2 and 6.3 of the AA, the Panel did not find it necessary to conduct an assessment of the alternative claim under Art. 7.2(b).", "keywords": ["agriculture & food"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS512", "title": "RUSSIA – TRAFFIC IN TRANSIT", "complainant": "Ukraine, Accession", "respondent": "Russia", "third_parties": [], "agreements": ["GATT Art. XX1(b), Russia’s Protocol of"], "articles": [], "subject": "", "sector": "Other", "year": 2019, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2019", "summary_ar": "", "summary_en": "• GATT 1994 Art. XXI(b)(iii) (national security exception not totally self-judging – measures taken in an emergency in international relations): The Panel interpreted Art. XXI(b) as vesting in panels the power to review whether the requirements of the enumerated subparagraphs were met, rather than leaving it to the unfettered discretion of the invoking Member. Accordingly, the Panel rejected the Russian Federation’s argument that the Panel lacked jurisdiction to review the Russian Federation’s invocation of Art. XXI(b)(iii). The Panel considered that an “emergency in international relations” referred generally to a situation of armed conflict, or of latent armed conflict, or of heightened tension or crisis, or of general instability engulfing and surrounding a state. Both the existence of an “emergency in international relations” and whether the action was “taken in time of” such emergency, within the meaning of subparagraph (iii) of Art. XXI(b), were subject to objective determination", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS513", "title": "MOROCCO – HOT-ROLLED STEEL (TURKEY)", "complainant": "Turkey", "respondent": "Morocco", "third_parties": [], "agreements": ["ADA Arts. 3.1, 3.4, 5.10, 6.8, 6.9"], "articles": [], "subject": "Definitive anti-dumping measures imposed by Morocco on imports from, among others, Turkey.", "sector": "Metals & Mining", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 5.10 (time-limit for conclusion of investigation): The Panel found that Morocco had acted inconsistently with Art. 5.10 by failing to conclude the investigation within the 18-month maximum time limit set out in that provision. • ADA Art. 3.1 (injury determination – establishment of domestic industry): The Panel found that Morocco had acted inconsistently with Art.3.1 in determining that the domestic industry was “unestablished”. • ADA Arts. 3.1 and 3.4 (injury determination): The Panel found that Morocco had acted inconsistently with Arts. 3.1 and 3.4 by improperly conducting the injury analysis in the form of “material retardation of the establishment of the domestic industry”. The Panel found that the investigating authority had (i) failed to evaluate five of the 15 injury factors listed in Art 3.4; (ii) disregarded the captive market in the injury analysis; and (iii) relied in the injury analysis on a particular report without properly investigating the significance of in", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS529", "title": "AUSTRALIA – ANTI-DUMPING MEASURES ON PAPER", "complainant": "Indonesia", "respondent": "Australia", "third_parties": [], "agreements": ["ADA Arts. 2.2, 2.2.1.1, 9.3"], "articles": [], "subject": "Anti-dumping measure imposed on imports from Indonesia following an anti-dumping investigation by the Australian Anti-Dumping Commission (ADC).", "sector": "Anti-Dumping", "year": 2020, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2020", "summary_ar": "", "summary_en": "• ADA Art. 2.2: (dumping determination – particular market situation): Prior to this Panel, no panel or AB report had interpreted the phrase “particular market situation” as it appears in Art. 2.2, which provides for the discarding of domestic sales as the basis for normal value when “because of a particular market situation … such sales do not permit a proper comparison”. 2 The Panel found that a “particular market situation” is only relevant insofar as it has the effect of rendering domestic sales unfit to permit a proper comparison, and further found that the phrase does not lend itself to a definition that foresees all the varied situations that an investigating authority may encounter that would fail to permit a “proper comparison”. The Panel found that a fact-specific and case-by-case analysis was necessarily called for. On this basis, the Panel did not accept Indonesia’s position that the phrase necessarily excludes: (i) situations where input costs of the product are allegedly ", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS316", "title": "EC AND CERTAIN MEMBER STATES – LARGE CIVIL AIRCRAFT", "complainant": "United States", "respondent": "European Union", "third_parties": [], "agreements": ["ASCM Arts. 1, 2, 5, 6.3, 7.8"], "articles": [], "subject": "Launch Aid/Member State Financing (LA/MSF) provided by France, German, Spain and the United Kingdom for the Airbus A350XWB and A380 LCA models that was found to have caused adverse effects in the orig", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "ASCM Art. 7.8 (remove adverse effects or withdraw the subsidy): • A380 LA/MSF: The Panel rejected the European Union's argument that amendments to the French, German, Spanish and UK A380 LA/MSF agreements achieved the withdrawal of the subsidy for purposes of Art. 7.8. The Panel concluded that the European Union failed to demonstrate that a commercial lender, faced with the likely termination of the A380 programme, would have entered into the A380 LA/MSF amendments on the terms agreed between Airbus and the relevant member State governments. The Panel also rejected that the Spanish A380 LA/MSF subsidy had been withdrawn as a result of the alleged amortization of the pre-existing subsidy, or that Airbus' announcement to terminate the A380 programme by 2021 achieved the withdrawal of the A380 LA/MSF subsidies. • A350 LA/MSF: The Panel rejected the European Union's argument that modifications to the German A350XWB LA/MSF agreement meant that the pre-existing subsidy had been replaced by a", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS371", "title": "THAILAND – CIGARETTES (PHILIPPINES) (ARTICLE 21.5 – PHILIPPINES II)", "complainant": "Philippines", "respondent": "Thailand", "third_parties": [], "agreements": ["CVA Arts. 1, 6, 7"], "articles": [], "subject": "Two sets of measures, including: (i) a set of criminal charges filed in 2017 accusing the importer of underdeclaring the customs values for 780 entries of cigarettes between 2002-2003; and (ii) 1,052 ", "sector": "Other", "year": 2018, "status": "Compliance", "stage": "Compliance", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2018", "summary_ar": "", "summary_en": "• CVA Art. 1.1 and 1.2(a) (valuation in a related-party transaction): The Charges violated Art. 1.1 and/or the substantive obligation in Art. 1.2(a), second sentence, of the CVA by rejecting the importer's declared transaction values without conducting a proper examination of the circumstances surrounding the sale, and/or a proper determination of the price actually paid or payable. • CVA Art. 6 and 7 (valuation based on computed value / reasonable means): The Charges violated Art. 6.1 and/or Art. 7.1 of the CVA by improperly relied on pricing and cost information reported by the manufacturer in certain tax forms to determine the revised customs value of the imported goods. • CVA Arts. 2-7 (sequential use of valuation methods): The Public Prosecutor violated the obligation to sequentially apply the customs valuation methods in Arts. 2 through 7 of the CVA when it determined the revised customs values of the imported goods. • GATT Art. XX (general exceptions): The general exceptions in ", "keywords": ["other", "CVA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS533", "title": "US – SOFTWOOD LUMBER VII", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ASCM Arts. 1.1, 11, 14, 19.4"], "articles": [], "subject": "Countervailing measures imposed by the United States.", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Art. 14(d) (calculation of amount of subsidy – rejection of benchmarks): The Panel found that the US investigation authority (USDOC) improperly rejected as appropriate stumpage benchmarks: (i) certain private market prices in Ontario; (ii) the British Columbia Timber Sales (BCTS) auction prices; (iii) auction stumpage prices in Québec; (iv) log prices in Alberta. The Panel also found that the USDOC's use of benchmark prices from Nova Scotia was inconsistent with ASCM Art. 14(d), as the USDOC erroneously found that the Nova Scotia benchmark price reasonably reflected the prevailing market conditions in certain provinces where the good was provided. Further, the Panel found that the USDOC acted inconsistently with ASCM Art. 14(d) because it did not make necessary adjustments to the Nova Scotia benchmark price such that the benchmark price related to the prevailing market conditions in the market where the good was provided. • ASCM Arts. 14 and 19.4 and GATT Art. VI:3 (reliance on ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS534", "title": "US – DIFFERENTIAL PRICING METHODOLOGY", "complainant": "Canada", "respondent": "United States", "third_parties": [], "agreements": ["ADA Arts. 1, 2.1 and 2.4.2"], "articles": [], "subject": "", "sector": "Anti-Dumping", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Anti-Dumping السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Art. 2.4.2 (dumping – identification of pattern): The USDOC found “a single pattern” of export prices “which differed significantly among different purchasers, regions and time periods”. This pattern included export prices to purchasers, regions or time periods that differed significantly because they were significantly higher than export prices to other purchasers, regions or time periods. The parties disagreed on whether, as a matter of law, the pattern clause permits an investigating authority to find such a “pattern”. The Panel found that (i) in applying the differential pricing methodology (DPM), and specifically under the ratio test, the USDOC had acted inconsistently with the second sentence of ADA Art. 2.4.2 because it had aggregated differences in export prices across unrelated categories, i.e. purchasers, regions and time periods to identify a single pattern of export prices which differed significantly among different purchasers, regions and time periods; but that (ii)", "keywords": ["anti-dumping", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS541", "title": "INDIA – EXPORT RELATED MEASURES", "complainant": "United States", "respondent": "India", "third_parties": [], "agreements": ["ASCM Arts. 1, 3.1(a), 27; Annexes"], "articles": [], "subject": "Exemptions from, or reductions of, customs duties or taxes, and granting by the government of India of freely transferable notes (scrips) to be used to satisfy certain liabilities vis-à-vis the govern", "sector": "Subsidies & Anti-Subsidy", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Subsidies & Anti-Subsidy السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ASCM Art. 27.2(b) (special and differential treatment of developing countries): The Panel rejected India’s argument that following its graduation from Art. 27.2(a) and Annex VII(b), the prohibition in Art. 3.1(a) still did not apply to its subsidy schemes, as a result of Art. 27.2(b). India did not fall under Art. 27.2, because (i) it had graduated from Annex VII(b) and ASCM Art. 27.2(a); and (ii) Art. 27.2(b) had expired on 1 January 2003, also for Members graduating from Annex VII(b). • ASCM footnote 1 (measures not deemed to be a subsidy): The Panel rejected India’s argument that the customs duties and excise taxes under the EOU/EHTP/BTP Schemes and the EPCG Scheme, and the MEIS scrips had to be deemed not to be subsidies in application of footnote 1. The Panel found that these measures did not meet the conditions set out in footnote 1 read together with Annexes I(g), I(h), and I(i). Some of the exemptions under the DFIS met these conditions and were deemed not to be subsidies. • ", "keywords": ["subsidies & anti-subsidy", "ASCM"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS556", "title": "US – STEEL AND ALUMINIUM (CHINA), US – STEEL AND ALUMINIUM", "complainant": "Norway, China, Switzerland", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. I.1; II:1;"], "articles": [], "subject": "Duties and related measures imposed by the United States on steel and aluminium imports under Section 232 of the Trade Expansion Act of 1962, as amended.", "sector": "Metals & Mining", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• GATT Art. II:1 (schedules of concessions): The Panels found that the duties on steel and aluminium were inconsistent with Art. II:1 as they exceeded the bound tariff rates in the United States’ WTO Schedule of Concessions. • GATT Art. I:1 (most-favoured-nation treatment): The Panels found that exemptions from the duties granted to steel and aluminium products from certain countries were inconsistent with the requirement of most-favoured-nation treatment under Art. I:1. • GATT Art. XI:1 (prohibition on quantitative restrictions): The Panels found that quotas on steel and aluminium products from certain countries were inconsistent with the requirement to eliminate quantitative restrictions under Art. XI:1 (only in DS552; DS556; DS564). • GATT Art. XXI(b)(iii) (national security exception): The Panels did not find based on the evidence and arguments submitted by the parties that the measures were “taken in time of war or other emergency in international relations”. Accordingly, the Pane", "keywords": ["metals & mining", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS553", "title": "KOREA – STAINLESS STEEL BARS", "complainant": "Japan", "respondent": "Korea", "third_parties": [], "agreements": ["ADA Arts. 6.5, 6.8, 11.3, 11.4"], "articles": [], "subject": "Third sunset review by the Korean investigating authority (KIA) of anti-dumping duties on certain stainless steel bars (SSB) from Japan.", "sector": "Metals & Mining", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "MEDIUM", "saudi_impact": "قد تؤثر على قطاع Metals & Mining السعودي", "request_date": "2018", "summary_ar": "", "summary_en": "• ADA Art. 11.3 (review of anti-dumping duties – likelihood of recurrence of injury – price and volume effects): Japan argued the KIA’s conclusion that “it is highly likely that once the anti-dumping measures are terminated, a drop in the price of the product under investigation and an increase in imports will again cause material injury to the domestic industry” rested on a defective analysis of the likely consequences of the Japanese price drop. The Panel considered that (i) the KIA had failed to engage in an unbiased and objective evaluation of the facts when concluding that domestic price competitiveness would be weakened by the Japanese pricing level resulting from the removal of the anti-dumping duty from the average Japanese resale price; and that (ii) by failing to address how the significantly higher-priced Japanese imports could increase in a price-sensitive market, the KIA’s determination had failed to resolve a tension in its own findings, and accordingly, it did not reflec", "keywords": ["metals & mining", "ADA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS567", "title": "SAUDI ARABIA – PROTECTION OF IPRS", "complainant": "Qatar", "respondent": "Saudi Arabia", "third_parties": [], "agreements": ["TRIPS Arts. 3.1, 4, 9, 14.3, 16.1, 41.1,"], "articles": [], "subject": "Measures relating to the piracy by beoutQ, a broadcasting entity, of the proprietary content of beIN, a global sports and entertainment company headquartered in Qatar. 2. SUMMARY OF KEY PANEL FINDINGS", "sector": "Intellectual Property", "year": 2018, "status": "Completed", "stage": "Completed", "saudi_relevance": "HIGH", "saudi_impact": "تأثير مباشر على مصالح المملكة", "request_date": "2018", "summary_ar": "", "summary_en": "• Panel’s jurisdiction (DSU Arts. 3.4, 3.7 and 11): The Panel found that it could not decline to exercise its jurisdiction over the claims of WTO-inconsistency that fell within its terms of reference and that the matter was justiciable. • TRIPS Arts. 41.1 (general obligations) and 42 (civil and administrative procedures and remedies): The Panel found that Saudi Arabia had acted inconsistently with TRIPS Art. 42 by taking measures that, directly or indirectly, had had the result of preventing beIN from obtaining Saudi legal counsel to enforce its IP rights through civil enforcement procedures before Saudi courts and tribunals (i.e. anti-sympathy measures). The Panel also considered that this violation of TRIPS Art. 42 had given rise to a consequential violation by Saudi Arabia of the obligation under TRIPS Art. 41 to “ensure that enforcement procedures as specified in this Part are available under their law”. • TRIPS Art. 61 (criminal procedures): The Panel found that Saudi Arabia had a", "keywords": ["intellectual property", "TRIPS"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS592", "title": "INDONESIA – RAW MATERIALS", "complainant": "European Union", "respondent": "Indonesia", "third_parties": [], "agreements": ["GATT Arts. XI, XI:2(a), XX(d)"], "articles": [], "subject": "A prohibition on the exportation of nickel ore (export ban) and a domestic processing requirement (DPR) whereby all nickel ore had to be processed (purified or refined) in Indonesia.", "sector": "Other", "year": 2021, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2021", "summary_ar": "", "summary_en": "• GATT Arts. XI:1 and XI:2(a) (quantitative restrictions): The Panel first considered whether the challenged measures fell within the scope of Art. XI. The Panel found that the export ban was a prohibition on the export of nickel ore. With respect to the DPR, the Panel found that it was a restriction within the meaning of Art. XI:1 even though it applied to all domestic actors irrespective of the destination of their goods. The Panel reasoned that because Art. XI:1 also covers measures prohibiting or restricting “sale for export” it applied to domestic regulations that prevent or limit the ability to sell goods for export. The Panel found that because domestic processing transforms nickel ore into another product, by requiring domestic processing prior to export, the DPR by its nature restricted the sale for export of nickel ore. The Panel concluded, therefore, that both measures were covered by the obligation in Art. XI:1. • GATT Art. XI:2(a) (prohibition on quantitative restrictions ", "keywords": ["other", "GATT"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}, {"ds_number": "DS597", "title": "US – ORIGIN MARKING (HONG KONG, CHINA)", "complainant": "China", "respondent": "United States", "third_parties": [], "agreements": ["GATT Arts. I:1, IX:1", "ROA Arts. 2(c), 2(d)", "TBT Art. 2.1"], "articles": [], "subject": "Requirement applied by the United States that imported goods produced in Hong Kong, China may no longer be marked to indicate “Hong Kong” as their origin, but must be marked to indicate “China” (origi", "sector": "Standards & TBT", "year": 2021, "status": "Completed", "stage": "Completed", "saudi_relevance": "LOW", "saudi_impact": "تأثير محدود", "request_date": "2021", "summary_ar": "", "summary_en": "• GATT Art. XXI(b) (self-judging nature of Art. XXI(b)(iii)): The Panel examined the ordinary meaning of Art. XXI(b), focusing on the grammatical structure of the provision in the three authentic languages, and found that the phrase “which it considers” in the chapeau of Article XXI(b) does not extend to the subparagraphs following the chapeau. The Panel tested this meaning against the context of Art. XXI(b) and the object and purpose of the covered agreements and confirmed that it made sense. It concluded that Art. XXI(b) was only partly self-judging in that the subparagraphs were not subject solely to the invoking Member’s own determination, but were, instead, subject to review by a panel. The Panel thus rejected the United States’ request to (only) find that the United States had invoked its essential security interests and to so report to the DSB. Instead, the Panel proceeded to examine whether the United States had breached its obligation under GATT Art. IX:1. • GATT Art. IX:1: Th", "keywords": ["standards & tbt", "GATT", "ROA"], "source": "WTO One-Page Case Summaries 1995-2022 (Official WTO Publication)"}]

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
