from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from receptive.models import Exercise, Question, Option, Attempt, Answer


class Command(BaseCommand):
    help = "Khoi tao toan bo du lieu mau Reading va Listening (6 bai moi ky nang, 5 cau hoi moi bai, giai thich tieng Anh de hieu)"

    def handle(self, *args, **options):
        self.stdout.write("Dang cap nhat va khoi tao lai co so du lieu...")

        # 1. Reset attempts and exercises de cap nhat du lieu moi nhat
        Answer.objects.all().delete()
        Attempt.objects.all().delete()
        Option.objects.all().delete()
        Question.objects.all().delete()
        Exercise.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("[OK] Da don dep du lieu cu de nap du lieu moi."))

        # 2. Tao Group HOC_VIEN
        group_hoc_vien, _ = Group.objects.get_or_create(name="HOC_VIEN")
        self.stdout.write(self.style.SUCCESS("[OK] Group HOC_VIEN: San sang."))

        # 3. Tai khoan Superusers & Hoc vien
        admin_u, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@dol.vn"})
        admin_u.set_password("admin123")
        admin_u.is_staff = True
        admin_u.is_superuser = True
        admin_u.first_name = "DOL"
        admin_u.last_name = "Admin"
        admin_u.save()

        mp_u, _ = User.objects.get_or_create(username="minhphuoc", defaults={"email": "minhphuoc@dol.vn"})
        mp_u.set_password("123456")
        mp_u.is_staff = True
        mp_u.is_superuser = True
        mp_u.first_name = "Minh"
        mp_u.last_name = "Phuoc"
        mp_u.groups.add(group_hoc_vien)
        mp_u.save()

        hv_u, _ = User.objects.get_or_create(username="hocvien", defaults={"email": "hocvien@dol.vn"})
        hv_u.set_password("hocvien123")
        hv_u.first_name = "Nguyen"
        hv_u.last_name = "Van Hoc"
        hv_u.groups.add(group_hoc_vien)
        hv_u.save()
        self.stdout.write(self.style.SUCCESS("[OK] Cac tai khoan (admin, minhphuoc, hocvien) da san sang."))

        # =========================================================================
        # 4. DANH SACH 6 BAI READING (Beginner, Intermediate, Advanced)
        # =========================================================================
        reading_data = [
            # ----------------- READING 1 (Beginner) -----------------
            {
                "title": "The Evolution of Urban Transportation: The Bicycle",
                "topic": "Technology & Urban Life",
                "level": Exercise.Level.BEGINNER,
                "description": "The historical development of bicycles and their vital role in modern sustainable urban transit.",
                "passage": (
                    "The history of the modern bicycle is a story of continuous technological innovation and social transformation. "
                    "In 1817, German inventor Baron Karl von Drais developed the 'Laufmaschine' (running machine), a two-wheeled wooden vehicle propelled by the rider pushing their feet against the ground. "
                    "Although clumsy by modern standards, it established the fundamental principle of two wheels in tandem.\n\n"
                    "Over the subsequent decades, European mechanics added pedals and rotary cranks to the front wheel, leading to the famous 'penny-farthing' with its enormous front wheel. "
                    "However, it was not until the 1880s that the 'Safety Bicycle' appeared, featuring equal-sized wheels and a chain drive linked to the rear axle. "
                    "Shortly after, John Boyd Dunlop invented the pneumatic rubber tire, which absorbed road vibrations and made cycling dramatically more comfortable and accessible to the general public.\n\n"
                    "In the twenty-first century, the bicycle has experienced a remarkable renaissance. With cities facing escalating traffic congestion and air pollution, urban planners are redesigning public infrastructure around two-wheeled transit. "
                    "In Copenhagen, extensive segregated bike superhighways have helped cycling surpass motor vehicles as the predominant mode of transport, accounting for more than 40 percent of all daily commuter journeys. "
                    "Zero emissions during operation and minimal space requirements make the bicycle one of the greenest solutions for future smart cities."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Where was the earliest steerable two-wheeled vehicle invented?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A (Germany). The text clearly states in paragraph 1 that 'German inventor Baron Karl von Drais developed the Laufmaschine in 1817.'",
                        "options": [
                            ("A", "Germany"),
                            ("B", "France"),
                            ("C", "England"),
                            ("D", "Netherlands"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Dunlop's pneumatic tire significantly increased cycling comfort for everyday riders.",
                        "correct_answers": ["True"],
                        "explanation": "Correct Answer: True. Paragraph 2 explicitly mentions that Dunlop's air-filled tires 'absorbed road vibrations and made cycling dramatically more comfortable and accessible'.",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "In Copenhagen, cycling represents more than ______ percent of daily commuter journeys.",
                        "correct_answers": ["40", "40%", "forty"],
                        "explanation": "Correct Answer: 40 (or 40%). Paragraph 3 confirms cycling accounts for 'more than 40 percent of all daily commuter journeys' in Copenhagen.",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is mentioned as a major urban advantage of cycling over cars?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B. The final sentence highlights 'Zero emissions during operation and minimal space requirements' as key urban advantages.",
                        "options": [
                            ("A", "High travel speeds across highway networks"),
                            ("B", "Zero greenhouse emissions and minimal space requirements"),
                            ("C", "Lower production costs compared to walking shoes"),
                            ("D", "Complete immunity from weather changes"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What key feature made the 1880s 'Safety Bicycle' different from earlier designs?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B. Paragraph 2 explains that the Safety Bicycle was distinguished by 'equal-sized wheels and a chain drive linked to the rear axle.'",
                        "options": [
                            ("A", "An oversized front wheel and no brakes"),
                            ("B", "Equal-sized wheels and a rear chain drive"),
                            ("C", "A lightweight carbon fiber frame"),
                            ("D", "Solid wooden tires without air tubes"),
                        ]
                    },
                ]
            },

            # ----------------- READING 2 (Beginner) -----------------
            {
                "title": "Coffee Culture and the Global Bean Trade",
                "topic": "Food & Agriculture",
                "level": Exercise.Level.BEGINNER,
                "description": "An exploration of coffee cultivation, global trade dynamics, and ethical farming certifications.",
                "passage": (
                    "Coffee is one of the most widely consumed beverages on Earth and the second most traded commodity after crude oil. "
                    "Botanical evidence indicates that Coffea arabica originally grew wild in the misty montane forests of southwestern Ethiopia. "
                    "According to popular legend, a ninth-century goat herder named Kaldi first observed how energized his herd became after nibbling on the plant's bright red berries.\n\n"
                    "From the Horn of Africa, cultivation spread across the Arabian Peninsula, where public coffee houses, known as 'qahveh khaneh', became vibrant cultural and intellectual hubs. "
                    "Today, coffee is cultivated throughout the equatorial region between the Tropics of Cancer and Capricorn, an area internationally recognized as the 'Bean Belt'. "
                    "Within this belt, volcanic soil, ample rainfall, and moderate temperatures provide ideal growing conditions.\n\n"
                    "The two primary commercial species are Arabica and Robusta (Coffea canephora). "
                    "Arabica thrives at high altitudes between 1,000 and 2,000 meters and is prized for its sweet, complex aromatic profile. "
                    "In contrast, Robusta grows well in lower, warmer elevations. Robusta beans contain nearly double the caffeine concentration of Arabica, which acts as a natural pesticide against insects, but produces a harsher, more bitter brew.\n\n"
                    "In recent years, fluctuating global commodity prices have placed enormous pressure on smallholder farmers. "
                    "In response, Fair Trade certifications have emerged to guarantee baseline pricing and support environmentally sustainable farming practices worldwide."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Where did wild Coffea arabica originally grow according to botanical records?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A (Ethiopian highlands). Paragraph 1 explicitly states that coffee 'originally grew wild in the misty montane forests of southwestern Ethiopia.'",
                        "options": [
                            ("A", "The misty highlands of southwestern Ethiopia"),
                            ("B", "The coastal valleys of South America"),
                            ("C", "The Mediterranean islands of Greece"),
                            ("D", "The tropical rainforests of Indonesia"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Robusta beans have a higher caffeine content than Arabica beans.",
                        "correct_answers": ["True"],
                        "explanation": "Correct Answer: True. Paragraph 3 clearly states: 'Robusta beans contain nearly double the caffeine concentration of Arabica.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "The equatorial zone where commercial coffee is grown is globally known as the ______.",
                        "correct_answers": ["Bean Belt", "bean belt", "The Bean Belt"],
                        "explanation": "Correct Answer: Bean Belt. Paragraph 2 mentions the area between the Tropics of Cancer and Capricorn is 'internationally recognized as the Bean Belt.'",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is a main purpose of Fair Trade certification in coffee farming?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. Paragraph 4 explains that Fair Trade certifications 'guarantee baseline pricing and support environmentally sustainable farming practices.'",
                        "options": [
                            ("A", "To secure fair minimum prices and promote eco-friendly farming"),
                            ("B", "To completely eliminate manual coffee bean harvesting"),
                            ("C", "To breed genetically modified coffee beans with zero caffeine"),
                            ("D", "To restrict coffee sales exclusively to European markets"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Does Arabica coffee produce a harsher and more bitter taste than Robusta?",
                        "correct_answers": ["No"],
                        "explanation": "Correct Answer: No. Paragraph 3 clarifies that Arabica is prized for its 'sweet, complex aromatic profile', whereas Robusta produces the harsher, bitter brew.",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            },

            # ----------------- READING 3 (Intermediate) -----------------
            {
                "title": "The Secrets of Deep-Sea Bioluminescence",
                "topic": "Marine Biology & Ecology",
                "level": Exercise.Level.INTERMEDIATE,
                "description": "How deep-sea animals create biological light and its revolutionary applications in medical biotechnology.",
                "passage": (
                    "In the perpetual darkness of the deep ocean, thousands of meters beneath the surface, sunlight never penetrates. "
                    "Yet this abyss is far from pitch-black; instead, it glimmers with flashes and pulses of living light. "
                    "This phenomenon, known as bioluminescence, is produced by an estimated ninety percent of animals living in the open ocean waters.\n\n"
                    "Bioluminescence is fundamentally a chemical reaction requiring two essential components: a substrate molecule called luciferin and an enzyme named luciferase. "
                    "When luciferin reacts with oxygen in the presence of luciferase, light is generated with almost one hundred percent thermal efficiency, meaning virtually no energy is wasted as heat—often called 'cold light'.\n\n"
                    "Marine organisms employ this optical weaponry for diverse survival strategies. "
                    "Predators such as the anglerfish dangle a glowing lure directly in front of their jaws to entice unsuspecting prey. "
                    "Conversely, prey species use light for counter-illumination: by emitting downward-directed light from photophores along their underbellies, they match the faint ambient light filtering from above, eliminating their silhouette from predators hunting below.\n\n"
                    "In medical biotechnology, bioluminescent markers have revolutionized genetic research, allowing scientists to track cancer cell migration and virus replication in living tissues in real time."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Bioluminescence generates a substantial amount of heat during the chemical reaction.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. Paragraph 2 explains the reaction has nearly 100% thermal efficiency, with 'virtually no energy wasted as heat' (known as 'cold light').",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is the primary function of counter-illumination in deep-sea creatures?",
                        "correct_answers": ["C"],
                        "explanation": "Correct Answer: C. Paragraph 3 describes counter-illumination as emitting light from underbellies to match downwelling light, 'eliminating their silhouette from predators hunting below.'",
                        "options": [
                            ("A", "To illuminate food on the ocean floor"),
                            ("B", "To communicate complex signals with distant mates"),
                            ("C", "To disguise their shadow and escape predators hunting from beneath"),
                            ("D", "To warm their body fluids in icy waters"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What is the name of the enzyme that catalyzes bioluminescent light production?",
                        "correct_answers": ["luciferase"],
                        "explanation": "Correct Answer: luciferase. Paragraph 2 names the enzyme 'luciferase', which acts on the substrate molecule luciferin.",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Are bioluminescent molecules used to observe living cancer cells in medical research?",
                        "correct_answers": ["Yes"],
                        "explanation": "Correct Answer: Yes. Paragraph 4 confirms that bioluminescent markers allow scientists 'to track cancer cell migration and virus replication in living tissues in real time.'",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Approximately what proportion of open ocean animals are estimated to be bioluminescent?",
                        "correct_answers": ["C"],
                        "explanation": "Correct Answer: C (Around 90%). The first paragraph highlights that bioluminescence is produced by 'an estimated ninety percent of animals living in the open ocean waters.'",
                        "options": [
                            ("A", "About 25 percent"),
                            ("B", "Nearly 50 percent"),
                            ("C", "Roughly 90 percent"),
                            ("D", "Fewer than 10 percent"),
                        ]
                    },
                ]
            },

            # ----------------- READING 4 (Intermediate) -----------------
            {
                "title": "Renewable Energy Storage: Beyond Lithium-Ion",
                "topic": "Energy & Sustainability",
                "level": Exercise.Level.INTERMEDIATE,
                "description": "Technological alternatives for utility-scale electrical storage: flow batteries, gravity, and thermal systems.",
                "passage": (
                    "As global electricity generation shifts toward solar photovoltaics and wind turbines, a profound engineering dilemma emerges: intermittency. "
                    "The sun does not always shine when power demand peaks, nor does the wind blow steadily. "
                    "While lithium-ion batteries dominate electric vehicles and consumer smartphones, their suitability for utility-scale grid balancing over days or weeks remains deeply constrained by high material costs, thermal runaway risks, and capacity degradation after thousands of rapid cycles.\n\n"
                    "Consequently, scientists are accelerating the deployment of alternative bulk storage solutions. "
                    "Foremost among these are redox flow batteries, particularly those utilizing vanadium electrolytes. "
                    "Unlike conventional batteries with solid electrodes, flow batteries store energy in large external tanks containing liquid chemical solutions. "
                    "Because energy capacity is decoupled from power output, scaling up storage simply involves building larger tanks of liquid, which do not degrade over decades of continuous operation.\n\n"
                    "Mechanical energy storage also offers enormous scalability. Pumped hydroelectric storage—pumping water up to a high elevation reservoir and releasing it through hydro-turbines during peak demand—still accounts for over ninety percent of global utility storage capacity. "
                    "Emerging gravity systems replicate this concept using heavy composite blocks raised by electric cranes, proving that the future of clean energy storage is remarkably multifaceted."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is identified as a major challenge for solar and wind energy grids?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A (Intermittency). Paragraph 1 explicitly names 'intermittency' as the central engineering dilemma because weather does not match peak power demand.",
                        "options": [
                            ("A", "Intermittent power generation that does not always match demand"),
                            ("B", "Lack of transmission power lines between major cities"),
                            ("C", "Inability of solar panels to produce electricity in summer"),
                            ("D", "Excessive maintenance costs of mechanical wind blades"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.TFNG,
                        "question_text": "In vanadium redox flow batteries, energy capacity is separated from power output.",
                        "correct_answers": ["True"],
                        "explanation": "Correct Answer: True. Paragraph 2 explains: 'Because energy capacity is decoupled from power output, scaling up storage simply involves building larger tanks of liquid.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "Which chemical element is predominantly utilized in the liquid electrolytes of redox flow batteries?",
                        "correct_answers": ["vanadium", "Vanadium"],
                        "explanation": "Correct Answer: vanadium. Paragraph 2 specifies 'redox flow batteries, particularly those utilizing vanadium electrolytes.'",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What type of storage currently accounts for over 90% of global utility storage capacity?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B (Pumped hydro storage). Paragraph 3 notes: 'Pumped hydroelectric storage... still accounts for over ninety percent of global utility storage capacity.'",
                        "options": [
                            ("A", "Subterranean compressed air caverns"),
                            ("B", "Pumped hydroelectric reservoir storage"),
                            ("C", "Lithium-ion mega-battery farms"),
                            ("D", "Molten salt solar towers"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Flow battery electrolytes degrade and lose capacity within two years of operation.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. Paragraph 2 explicitly highlights that flow battery solutions 'do not degrade over decades of continuous operation.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            },

            # ----------------- READING 5 (Advanced) -----------------
            {
                "title": "Cognitive Linguistics and Linguistic Relativity",
                "topic": "Psychology & Linguistics",
                "level": Exercise.Level.ADVANCED,
                "description": "An academic investigation into whether linguistic structures actively shape human thought and perception.",
                "passage": (
                    "Does the language we speak influence the way we perceive and categorize the world? "
                    "This enduring intellectual riddle lies at the heart of the Linguistic Relativity Hypothesis, colloquially known as the Sapir-Whorf hypothesis. "
                    "Formulated during the first half of the twentieth century by linguist Edward Sapir and his student Benjamin Lee Whorf, the conjecture suggests that distinct grammatical and lexical structures predispose speakers toward different habitual ways of thinking.\n\n"
                    "Scholars historically divided the hypothesis into two versions: linguistic determinism (the strong version) and linguistic relativity (the weak version). "
                    "Determinism claims that language strictly dictates thought boundaries, implying that concepts unexpressed in one's native lexicon cannot be comprehended. "
                    "This extreme view has been largely discredited by modern cognitive neuroscience, which proves that conceptual cognition frequently operates independently of verbal language.\n\n"
                    "In contrast, the weaker version of linguistic relativity has received convincing empirical validation in recent decades. "
                    "Cross-linguistic experiments show that speakers of languages that assign grammatical gender to inanimate objects attribute distinct traits to those objects. "
                    "Similarly, Russian speakers, whose language has separate basic terms for light blue (goluboy) and dark blue (siniy), discriminate between shades of blue faster than English speakers. "
                    "Rather than imprisoning human thought, language functions as an optical lens, subtly directing attention to specific aspects of experiential reality."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "How does modern cognitive neuroscience view 'linguistic determinism'?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B. Paragraph 2 explains that strict determinism has been 'largely discredited' because conceptual cognition operates independently of verbal language.",
                        "options": [
                            ("A", "As conclusively validated through brain imaging trials"),
                            ("B", "As largely discredited because human thought exists without verbal labels"),
                            ("C", "As identical in every respect to linguistic relativity"),
                            ("D", "As valid only when applied to computer programming codes"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Russian speakers distinguish shades of blue more rapidly than English speakers.",
                        "correct_answers": ["True"],
                        "explanation": "Correct Answer: True. Paragraph 3 affirms that Russian speakers 'discriminate between shades of blue faster than English speakers' due to distinct lexical categories.",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "Which linguist and student formulated the foundational hypothesis of linguistic relativity?",
                        "correct_answers": ["sapir and whorf", "sapir-whorf", "edward sapir and benjamin whorf"],
                        "explanation": "Correct Answer: Sapir and Whorf. Paragraph 1 credits linguist Edward Sapir and his student Benjamin Lee Whorf.",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "How does the author metaphorically describe the function of language in cognition?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B. The final sentence states: 'Rather than imprisoning human thought, language functions as an optical lens, subtly directing attention.'",
                        "options": [
                            ("A", "As an impenetrable prison cell for the human mind"),
                            ("B", "As an optical lens focusing attention on certain aspects of reality"),
                            ("C", "As a decorative mirror reflecting genetic instincts"),
                            ("D", "As an automated calculator processing numbers"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Does grammatical gender in language influence how people describe inanimate objects?",
                        "correct_answers": ["Yes"],
                        "explanation": "Correct Answer: Yes. Paragraph 3 points out that experiments demonstrate speakers 'attribute distinct traits to objects' based on assigned grammatical gender.",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            },

            # ----------------- READING 6 (Advanced) -----------------
            {
                "title": "The Architecture of Ancient Roman Concrete",
                "topic": "Archaeology & Materials Science",
                "level": Exercise.Level.ADVANCED,
                "description": "The chemical marvels of Roman marine concrete, volcanic pozzolana, and self-healing crystalline structures.",
                "passage": (
                    "While modern marine concrete structures frequently crack and deteriorate within fifty years of aggressive saltwater exposure, two-thousand-year-old Roman piers and breakwaters continue to withstand the relentless battering of oceanic tides. "
                    "For centuries, the enduring durability of Roman maritime architecture, known as 'opus caementicium', puzzled civil engineers and materials scientists alike.\n\n"
                    "Recent geological and spectroscopic analyses have illuminated the secret ingredient: volcanic ash, particularly pozzolana harvested from deposits around the Gulf of Naples. "
                    "Roman builders mixed this volcanic pozzolana with slaked lime and seawater to form a resilient mortar. "
                    "Crucially, the lime was blended using a hot-mixing method, leaving small white mineral inclusions called 'lime clasts' scattered throughout the matrix.\n\n"
                    "When seawater permeates micro-fissures in Roman concrete, it reacts with these lime clasts and surrounding volcanic minerals to precipitate rare crystals called aluminous tobermorite and phillipsite. "
                    "Rather than deteriorating the material, the seawater actually triggers a secondary chemical reaction that weaves interlocking crystals into the cracks, effectively conferring a 'self-healing' capability upon the structure.\n\n"
                    "Modern engineers are now seeking to reverse-engineer Roman formulations. "
                    "Because modern Portland cement requires fossil-fuel-intensive kilns heated to 1,450 degrees Celsius—responsible for roughly eight percent of global carbon dioxide emissions—adopting low-temperature pozzolanic concrete could revolutionize sustainable civil engineering."
                ),
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What primary volcanic material gave Roman marine concrete its extraordinary resilience?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A (Pozzolana ash). Paragraph 2 identifies 'volcanic ash, particularly pozzolana harvested from deposits around the Gulf of Naples' as the key ingredient.",
                        "options": [
                            ("A", "Pozzolanic volcanic ash from the Gulf of Naples"),
                            ("B", "Synthetic epoxy resin binders"),
                            ("C", "Crushed marble powder from northern Italy"),
                            ("D", "Granite gravel quarried from Egypt"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Prolonged exposure to seawater gradually broke down and destroyed Roman harbour walls.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. Paragraph 3 explains that seawater actually reacted with minerals to grow interlocking crystals that strengthened rather than degraded the structures.",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What rare mineral crystal precipitates inside micro-cracks to give Roman concrete self-healing properties?",
                        "correct_answers": ["tobermorite", "aluminous tobermorite", "al-tobermorite"],
                        "explanation": "Correct Answer: tobermorite (or aluminous tobermorite). Paragraph 3 specifies that seawater reaction precipitates 'rare crystals called aluminous tobermorite and phillipsite.'",
                        "options": []
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What environmental advantage could modern construction gain from ancient Roman cement principles?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. Paragraph 4 notes modern Portland cement generates 8% of global CO2 emissions due to 1450°C kilns; pozzolanic mixes cure at lower temperatures, slashing emissions.",
                        "options": [
                            ("A", "Significant reduction in high-temperature kiln emissions"),
                            ("B", "Complete elimination of freshwater use in agriculture"),
                            ("C", "Rapid drying times in less than ten minutes"),
                            ("D", "Transparent buildings that do not require windows"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Did Roman engineers rely on electronic microscopes to design their lime clast formula?",
                        "correct_answers": ["No"],
                        "explanation": "Correct Answer: No. Paragraph 1 and 2 clarify this was ancient craftsmanship developed 2,000 years ago, long before modern analytical microscopes existed.",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            }
        ]

        # Tao cac bai Reading
        for ex_info in reading_data:
            exercise = Exercise.objects.create(
                title=ex_info["title"],
                skill=Exercise.Skill.READING,
                topic=ex_info["topic"],
                level=ex_info["level"],
                description=ex_info["description"],
                passage=ex_info["passage"],
                status=Exercise.Status.PUBLISHED,
            )
            for q_info in ex_info["questions"]:
                q = Question.objects.create(
                    exercise=exercise,
                    order_no=q_info["order_no"],
                    question_type=q_info["question_type"],
                    question_text=q_info["question_text"],
                    correct_answers=q_info["correct_answers"],
                    explanation=q_info["explanation"],
                    status=Question.Status.PUBLISHED,
                )
                for opt_key, opt_text in q_info["options"]:
                    Option.objects.create(
                        question=q,
                        option_key=opt_key,
                        option_text=opt_text,
                        order_no=ord(opt_key[0]) if len(opt_key) == 1 else 1,
                    )
            self.stdout.write(self.style.SUCCESS(f"[OK] Da tao Reading ({exercise.level}): {exercise.title} (5 cau hoi)"))

        # =========================================================================
        # 5. DANH SACH 6 BAI LISTENING (Beginner, Intermediate, Advanced)
        # =========================================================================
        listening_data = [
            # ----------------- LISTENING 1 (Beginner) -----------------
            {
                "title": "Student Accommodation and Housing Enquiry",
                "topic": "Campus Life & Housing",
                "level": Exercise.Level.BEGINNER,
                "description": "A conversation between an international student, Alex, and a university housing officer, Mrs. Davis.",
                "audio_file": "listening/audio_exercise_1.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What is the student's maximum monthly budget including utilities? ($______)",
                        "correct_answers": ["450", "450 dollars", "$450"],
                        "explanation": "Correct Answer: 450 (or $450). Alex explicitly says: 'My maximum monthly budget is 450 dollars, ideally including utility bills.'",
                        "options": []
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Which accommodation option does the advisor recommend for international freshmen?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. Mrs. Davis advises: 'For first-year international students, we strongly recommend our University Residence Halls for security and community.'",
                        "options": [
                            ("A", "University Residence Hall"),
                            ("B", "Private Studio Apartment"),
                            ("C", "Suburban Shared House"),
                            ("D", "Homestay with a local family"),
                        ]
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What document must the student submit before next Friday to confirm the room?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. Mrs. Davis states: 'To secure your reservation, you must submit a scanned copy of your Student ID card before next Friday.'",
                        "options": [
                            ("A", "Scanned copy of Student ID card"),
                            ("B", "Official bank financial statement"),
                            ("C", "Medical health insurance letter"),
                            ("D", "Academic recommendation letter"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "Which specific residential hall matches Alex's budget?",
                        "correct_answers": ["Hall B", "hall b", "Hall B option"],
                        "explanation": "Correct Answer: Hall B. The housing officer explains that Alex's $450 budget 'fits nicely with our Hall B option.'",
                        "options": []
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Water and heating utilities are included in the Hall B monthly rent.",
                        "correct_answers": ["True"],
                        "explanation": "Correct Answer: True. Mrs. Davis confirms: 'Standard water and heating are included in this package.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            },

            # ----------------- LISTENING 2 (Beginner) -----------------
            {
                "title": "City Leisure Centre Registration & Facilities",
                "topic": "Sports & Community Life",
                "level": Exercise.Level.BEGINNER,
                "description": "A customer service staff member explains membership options, sports halls, and opening hours to a new visitor.",
                "audio_file": "listening/audio_exercise_2.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What time does the Olympic swimming pool open on weekday mornings?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A (6:00 AM). The officer notes: 'On weekdays, the swimming pool opens early at 6:00 AM for morning lap swimmers.'",
                        "options": [
                            ("A", "6:00 AM"),
                            ("B", "7:00 AM"),
                            ("C", "8:30 AM"),
                            ("D", "9:00 AM"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "How much does an annual student membership pass cost? (£______)",
                        "correct_answers": ["180", "180 pounds", "£180"],
                        "explanation": "Correct Answer: 180 (or £180). The representative says: 'an annual student pass is discounted to only 180 pounds per year.'",
                        "options": []
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Which activity requires advance booking at least 24 hours ahead?",
                        "correct_answers": ["C"],
                        "explanation": "Correct Answer: C. The staff explains: 'our indoor cycling spin class requires advance booking at least 24 hours ahead due to limited bikes.'",
                        "options": [
                            ("A", "Drop-in Yoga class"),
                            ("B", "Gym free weights area"),
                            ("C", "Indoor cycling spin class"),
                            ("D", "Lap swimming pool lanes"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.TFNG,
                        "question_text": "The changing room locker fee is non-refundable.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. The staff mentions that 'Lockers use a returnable one-pound coin deposit, so you get your money back.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What kind of soles must members' sports shoes have in the badminton courts?",
                        "correct_answers": ["rubber", "rubber soles", "non-marking rubber"],
                        "explanation": "Correct Answer: rubber (or non-marking rubber). The officer states: 'members must wear clean sports shoes with non-marking rubber soles.'",
                        "options": []
                    },
                ]
            },

            # ----------------- LISTENING 3 (Intermediate) -----------------
            {
                "title": "University Library Orientation and Research Services",
                "topic": "Academic Facilities",
                "level": Exercise.Level.INTERMEDIATE,
                "description": "An orientation tour of the university central library, loan privileges, and quiet study zones.",
                "audio_file": "listening/audio_exercise_3.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "On which floor are the silent study pods strictly located?",
                        "correct_answers": ["C"],
                        "explanation": "Correct Answer: C. The librarian instructs: 'if you require absolute quiet... please head up to the Third Floor. Level 3 is reserved strictly for silent research.'",
                        "options": [
                            ("A", "Ground Floor"),
                            ("B", "Second Floor"),
                            ("C", "Third Floor"),
                            ("D", "Basement Archive"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "How many books can postgraduate researchers borrow simultaneously?",
                        "correct_answers": ["15", "fifteen", "15 books"],
                        "explanation": "Correct Answer: 15 (or fifteen). The guide states: 'postgraduate researchers are entitled to borrow up to 15 books simultaneously.'",
                        "options": []
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Interlibrary loan services require a surcharge fee for enrolled students.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. The librarian emphasizes: 'our interlibrary loan service with partner institutions... is completely free of charge for all enrolled students.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Where is the general computer lab and printing area situated?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. The guide states: 'On the Ground Floor, you will find our main circulation desk... and the general computer lab with high-speed printing.'",
                        "options": [
                            ("A", "Ground Floor"),
                            ("B", "Second Floor mezzanine"),
                            ("C", "Third Floor east wing"),
                            ("D", "Outdoor reading garden"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What is the standard borrowing duration for postgraduate book loans in weeks?",
                        "correct_answers": ["4", "four", "4 weeks"],
                        "explanation": "Correct Answer: 4 (or four). The librarian specifies postgraduate books can be borrowed 'for a duration of four weeks.'",
                        "options": []
                    },
                ]
            },

            # ----------------- LISTENING 4 (Intermediate) -----------------
            {
                "title": "Sustainable Urban Transport Planning Interview",
                "topic": "Urban Planning & Environment",
                "level": Exercise.Level.INTERMEDIATE,
                "description": "A radio interview with Dr. Marcus Vance discussing the municipal green transit initiative and cycling networks.",
                "audio_file": "listening/audio_exercise_4.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What percentage drop in private car traffic occurred after the congestion charge?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B (24%). Dr. Vance states: 'passenger vehicle traffic in the central district dropped by 24 percent.'",
                        "options": [
                            ("A", "12 percent"),
                            ("B", "24 percent"),
                            ("C", "36 percent"),
                            ("D", "50 percent"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "By which target year will the entire municipal bus fleet be fully electric?",
                        "correct_answers": ["2030", "twenty thirty"],
                        "explanation": "Correct Answer: 2030. Dr. Vance confirms the city committed to 'electrifying our entire municipal bus fleet by the year 2030.'",
                        "options": []
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is the main design feature of the newly constructed transit interchanges?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. Dr. Vance explains: 'These hubs provide seamless, sheltered connections between trams, city buses, and secured bicycle parking.'",
                        "options": [
                            ("A", "Seamless sheltered connections between light rail, buses, and bikes"),
                            ("B", "Multi-level underground parking spaces for diesel vehicles"),
                            ("C", "Luxury retail shopping malls on every concourse"),
                            ("D", "Exclusive lanes reserved for private taxi fleets"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.TFNG,
                        "question_text": "Passengers must still purchase traditional paper tickets before boarding buses.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. Dr. Vance states: 'commuters no longer need paper tickets; our universal contactless payment system allows tapping with any smartphone or debit card.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What universal smart payment method enables commuters to tap smartphones or cards?",
                        "correct_answers": ["contactless", "contactless payment"],
                        "explanation": "Correct Answer: contactless. The speaker refers to 'our universal contactless payment system'.",
                        "options": []
                    },
                ]
            },

            # ----------------- LISTENING 5 (Advanced) -----------------
            {
                "title": "Marine Ecosystem Lecture: Coral Bleaching Mechanisms",
                "topic": "Environmental Science",
                "level": Exercise.Level.ADVANCED,
                "description": "An academic lecture examining thermal stress, zooxanthellae loss, and recovery thresholds in coral reefs.",
                "audio_file": "listening/audio_exercise_5.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What is the primary stressor causing corals to expel symbiotic algae?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. The lecturer states: 'When sea surface temperatures rise even one or two degrees Celsius... the coral experiences thermal stress' and expels zooxanthellae.",
                        "options": [
                            ("A", "Elevated sea surface temperatures"),
                            ("B", "Excessive ocean salinity"),
                            ("C", "Underwater sonic pollution"),
                            ("D", "Shifts in prevailing trade winds"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What percentage of energy do photosynthetic algae supply to healthy corals?",
                        "correct_answers": ["90", "90%", "ninety"],
                        "explanation": "Correct Answer: 90 (or 90%). The lecturer highlights: 'these algae supply up to 90 percent of the coral host's nutritional energy requirements.'",
                        "options": []
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Can bleached corals recover if temperature anomalies return to baseline quickly?",
                        "correct_answers": ["Yes"],
                        "explanation": "Correct Answer: Yes. The speaker emphasizes: 'If ambient water temperatures return to baseline within several weeks, bleached corals can reabsorb symbiotic microalgae and make a full recovery.'",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "Why does a bleached coral reef appear strikingly white?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. The professor explains: 'Because coral tissue is naturally translucent, shedding the pigmented algae exposes the stark white calcium carbonate skeleton beneath.'",
                        "options": [
                            ("A", "Translucent tissue reveals the white calcium carbonate skeleton beneath"),
                            ("B", "White toxic bacteria coat the ocean floor surface"),
                            ("C", "Marine salt dries out on shallow submerged rocks"),
                            ("D", "Chemical residues from oil tankers settle onto the reef"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "What is the biological name of the microscopic algae living symbiotically within coral tissues?",
                        "correct_answers": ["zooxanthellae"],
                        "explanation": "Correct Answer: zooxanthellae. The lecturer identifies the microscopic photosynthetic algae as 'zooxanthellae'.",
                        "options": []
                    },
                ]
            },

            # ----------------- LISTENING 6 (Advanced) -----------------
            {
                "title": "Archaeological Symposium: Aerial LiDAR Technology",
                "topic": "Archaeology & Remote Sensing",
                "level": Exercise.Level.ADVANCED,
                "description": "A symposium address on how laser scanning penetrates jungle canopies to reveal lost Mesoamerican cities.",
                "audio_file": "listening/audio_exercise_6.wav",
                "questions": [
                    {
                        "order_no": 1,
                        "question_type": Question.Type.MCQ,
                        "question_text": "How does airborne LiDAR penetrate dense tropical forest canopies?",
                        "correct_answers": ["A"],
                        "explanation": "Correct Answer: A. The speaker states LiDAR fires pulses from an aircraft, and 'enough photons filter through gaps in the leaves to measure ground topography.'",
                        "options": [
                            ("A", "Laser pulses filter through gaps between tree leaves to measure ground elevation"),
                            ("B", "Infrared heat beams burn away leaves to reveal buried temples"),
                            ("C", "Optical satellite cameras take close-up photos through cloud cover"),
                            ("D", "Acoustic sonar pulses bounce back from bedrock layers"),
                        ]
                    },
                    {
                        "order_no": 2,
                        "question_type": Question.Type.SHORT_TEXT,
                        "question_text": "LiDAR is an acronym for Light Detection and ______.",
                        "correct_answers": ["Ranging", "ranging"],
                        "explanation": "Correct Answer: Ranging. The archaeologist explicitly notes: 'aerial LiDAR—which stands for Light Detection and Ranging.'",
                        "options": []
                    },
                    {
                        "order_no": 3,
                        "question_type": Question.Type.TFNG,
                        "question_text": "LiDAR mapping revealed that ancient settlements were smaller and more isolated than once believed.",
                        "correct_answers": ["False"],
                        "explanation": "Correct Answer: False. The speaker stresses that 'Instead of isolated jungle settlements, LiDAR revealed massive interconnected urban networks.'",
                        "options": [
                            ("True", "True"),
                            ("False", "False"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                    {
                        "order_no": 4,
                        "question_type": Question.Type.MCQ,
                        "question_text": "What surprising agricultural systems did LiDAR scans expose under the jungle?",
                        "correct_answers": ["B"],
                        "explanation": "Correct Answer: B. The presentation highlights: 'we discovered vast networks of terraced agricultural hillsides and sophisticated irrigation canals.'",
                        "options": [
                            ("A", "Underground nuclear storage caverns"),
                            ("B", "Extensive terraced hillsides and sophisticated irrigation canals"),
                            ("C", "Modern hydro dams and metal bridges"),
                            ("D", "Paved four-lane vehicle highways"),
                        ]
                    },
                    {
                        "order_no": 5,
                        "question_type": Question.Type.YNNG,
                        "question_text": "Do specialized software algorithms need to filter out vegetation returns to create terrain models?",
                        "correct_answers": ["Yes"],
                        "explanation": "Correct Answer: Yes. The speaker points out: 'Specialized computer algorithms then strip away the vegetation returns to generate a digital bare-earth terrain model.'",
                        "options": [
                            ("Yes", "Yes"),
                            ("No", "No"),
                            ("Not Given", "Not Given"),
                        ]
                    },
                ]
            }
        ]

        # Tao cac bai Listening
        for ex_info in listening_data:
            exercise = Exercise.objects.create(
                title=ex_info["title"],
                skill=Exercise.Skill.LISTENING,
                topic=ex_info["topic"],
                level=ex_info["level"],
                description=ex_info["description"],
                audio_file=ex_info["audio_file"],
                status=Exercise.Status.PUBLISHED,
            )
            for q_info in ex_info["questions"]:
                q = Question.objects.create(
                    exercise=exercise,
                    order_no=q_info["order_no"],
                    question_type=q_info["question_type"],
                    question_text=q_info["question_text"],
                    correct_answers=q_info["correct_answers"],
                    explanation=q_info["explanation"],
                    status=Question.Status.PUBLISHED,
                )
                for opt_key, opt_text in q_info["options"]:
                    Option.objects.create(
                        question=q,
                        option_key=opt_key,
                        option_text=opt_text,
                        order_no=ord(opt_key[0]) if len(opt_key) == 1 else 1,
                    )
            self.stdout.write(self.style.SUCCESS(f"[OK] Da tao Listening ({exercise.level}): {exercise.title} (5 cau hoi)"))

        self.stdout.write(self.style.SUCCESS("=== HOAN TAT! 12 BAI LUYEN (6 READING, 6 LISTENING), 60 CAU HOI KEM GIAI THICH TIENG ANH DE HIEU ==="))
