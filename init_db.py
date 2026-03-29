from app import create_app
from app.models import (
    db, User, Student, Teacher, School, Section,
    Course, Enrollment, TimetableEntry, bcrypt,
    ProfessorAssistant
)
from datetime import datetime

app = create_app()

# =====================================================================
# DATA CONSTANTS
# =====================================================================

SECTION_1_STUDENTS = [
    {"name": "Lakkavaram Sripada Gayathri", "email": "sripadagayathri.l-29@scds.saiuniversity.edu.in"},
    {"name": "Ram Mouli", "email": "ram.m1-29@scds.saiuniversity.edu.in"},
    {"name": "Raghav Sudhakaran", "email": "raghav.s-29@scds.saiuniversity.edu.in"},
    {"name": "Jessika S", "email": "jessika.s-29@scds.saiuniversity.edu.in"},
    {"name": "Baladithya T", "email": "balaaditya.t-29@scds.saiuniversity.edu.in"},
    {"name": "Shilpa Sharma", "email": "shilpasharma.s-29@scds.saiuniversity.edu.in"},
    {"name": "Niharika D", "email": "niharika.d-29@scds.saiuniversity.edu.in"},
    {"name": "Santhosh Srinivasan", "email": "santhosh.s-29@scds.saiuniversity.edu.in"},
    {"name": "M Meera", "email": "meera.m-29@scds.saiuniversity.edu.in"},
    {"name": "R Sai Sanjay", "email": "saisanjay.r-29@scds.saiuniversity.edu.in"},
    {"name": "Dhanvanth Ravichandran", "email": "dhanvanth.r-29@scds.saiuniversity.edu.in"},
    {"name": "Sahana Mukundan", "email": "sahana.m-29@scds.saiuniversity.edu.in"},
    {"name": "Aitha Sree Sai Tanay", "email": "sreeasaitany.a-29@scds.saiuniversity.edu.in"},
    {"name": "Vaka Gayasree Reddy", "email": "gayasreereddy.v-29@scds.saiuniversity.edu.in"},
    {"name": "Sriguhan C S", "email": "sriguhan.c-29@scds.saiuniversity.edu.in"},
    {"name": "Shaik Mujimel", "email": "mujimel.s-29@scds.saiuniversity.edu.in"},
    {"name": "Cherukuri Hima Kethan", "email": "himakethan.c-29@scds.saiuniversity.edu.in"},
    {"name": "Vanka Vyoma Sai", "email": "vyomasai.v-29@scds.saiuniversity.edu.in"},
    {"name": "P Krishna Kishore", "email": "krishnakishore.p1-29@scds.saiuniversity.edu.in"},
    {"name": "Avula Disu Sandhya", "email": "sandhya.a-29@scds.saiuniversity.edu.in"},
    {"name": "A Uday Tej Reddy", "email": "uday.a-29@scds.saiuniversity.edu.in"},
    {"name": "Kavanoor Jeevana", "email": "jeevana.k-29@scds.saiuniversity.edu.in"},
    {"name": "Ane Rishendra", "email": "rishendra.a-29@scds.saiuniversity.edu.in"},
    {"name": "Hemasree R", "email": "hemasree.r-29@scds.saiuniversity.edu.in"},
    {"name": "Mahavadi Mohith Sarma", "email": "mohithsarma.m-29@scds.saiuniversity.edu.in"},
    {"name": "Ramachandruni V S Krishna Karthik", "email": "krishnakarthik.r-29@scds.saiuniversity.edu.in"},
    {"name": "Malladi Karthika", "email": "karthika.m-29@scds.saiuniversity.edu.in"},
    {"name": "Rokkam Shailesh Karthick", "email": "shaileshkarthick.r-29@scds.saiuniversity.edu.in"},
    {"name": "Kasya Lasya Gama Priya", "email": "lasyagamapriya.k-29@scds.saiuniversity.edu.in"},
    {"name": "Iska Lokesh Kumar", "email": "lokeshkumar.i-29@scds.saiuniversity.edu.in"},
    {"name": "Laki Reddy Varshini", "email": "varshini.l-29@scds.saiuniversity.edu.in"},
    {"name": "Kova Navitha Sai Sree", "email": "navithasaisree.k-29@scds.saiuniversity.edu.in"},
    {"name": "Ruthikka Arunkumar", "email": "ruthikka.a-29@scds.saiuniversity.edu.in"},
    {"name": "Kolluri Navya Vijaya Sree", "email": "navyavijayasree.k-29@scds.saiuniversity.edu.in"},
    {"name": "Palavali Midhun Reddy", "email": "midhunreddy.p-29@scds.saiuniversity.edu.in"},
    {"name": "Thummala Chetan Kumar", "email": "chetankumar.t-29@scds.saiuniversity.edu.in"},
    {"name": "Gopisetty Bhagya Varshini", "email": "bhagyavarshini.g-29@scds.saiuniversity.edu.in"},
    {"name": "Astakala Saketh", "email": "saketh.a-29@scds.saiuniversity.edu.in"},
    {"name": "Mulla Muhammed Maheboob", "email": "mullamuhammed.m-29@scds.saiuniversity.edu.in"},
    {"name": "Jarugula Amulya", "email": "amulya.j-29@scds.saiuniversity.edu.in"},
    {"name": "Gogireddy Vishnu Vardhan Reddy", "email": "vishnuvardhan.g-29@scds.saiuniversity.edu.in"},
    {"name": "Atmakuru Venkat Charan", "email": "venkatcharan.a-29@scds.saiuniversity.edu.in"},
    {"name": "D Advika", "email": "advika.d-29@scds.saiuniversity.edu.in"},
    {"name": "Shaik Mohammed Aymen", "email": "mohammedaymen.s-29@scds.saiuniversity.edu.in"},
    {"name": "Chembeti Guru Sai Charan", "email": "saicharan.c-29@scds.saiuniversity.edu.in"},
    {"name": "Narisetty Nithish Kumar", "email": "nithishkumar.n-29@scds.saiuniversity.edu.in"},
    {"name": "Buyyareddy Deepthi", "email": "deepthi.b-29@scds.saiuniversity.edu.in"},
    {"name": "Chembeti Tejesh", "email": "tejesh.c-29@scds.saiuniversity.edu.in"},
    {"name": "Aravabhumi Dharma Teja", "email": "dharmateja.a-29@scds.saiuniversity.edu.in"},
    {"name": "Salava Santhosh Kumar", "email": "santhoshkumar.s-29@scds.saiuniversity.edu.in"},
    {"name": "Subhan Sarangi", "email": "subhan.s-29@scds.saiuniversity.edu.in"},
    {"name": "Paladugu balaji", "email": "balaji.p-29@scds.saiuniversity.edu.in"},
    {"name": "Vemula Jayakrishna", "email": "jayakrishna.v-29@scds.saiuniversity.edu.in"},
    {"name": "Rayi Nishitha", "email": "nishitha.r-29@scds.saiuniversity.edu.in"},
    {"name": "Gurram Lokeswari", "email": "lokeswari.g-29@scds.saiuniversity.edu.in"},
    {"name": "P Sudeep", "email": "sudeep.p-29@scds.saiuniversity.edu.in"},
    {"name": "Madala Tejaswi", "email": "tejaswi.m-29@scds.saiuniversity.edu.in"},
    {"name": "Vemala Sailesh", "email": "sailesh.v-29@scds.saiuniversity.edu.in"},
    {"name": "Mallavarapu Sai Charan Kumar Reddy", "email": "saicharan.m1-29@scds.saiuniversity.edu.in"},
    {"name": "Medikonda Adithya Vardhan", "email": "adithyavardhan.m-29@scds.saiuniversity.edu.in"},
    {"name": "Nagaraju danaboena", "email": "nagaraju.d-29@scds.saiuniversity.edu.in"},
    {"name": "Shaik Shareef", "email": "shareef.s-29@scds.saiuniversity.edu.in"},
    {"name": "Pethuri N V L N Devamithra", "email": "devamithra.p-29@scds.saiuniversity.edu.in"},
    {"name": "Thiruvaipati Jahnavi", "email": "jahnavi.t-29@scds.saiuniversity.edu.in"},
    {"name": "Suru Yaswanth Reddy", "email": "yaswanthreddy.s-29@scds.saiuniversity.edu.in"},
    {"name": "Guduguntla Sahithi", "email": "sahithi.g-29@scds.saiuniversity.edu.in"},
    {"name": "Shaik Abdul Samad", "email": "abdulsamad.s-29@scds.saiuniversity.edu.in"},
    {"name": "Marripakula Teja", "email": "teja.m-29@scds.saiuniversity.edu.in"},
    {"name": "Buragadda Prasanth Sri", "email": "prasanthsri.b-29@scds.saiuniversity.edu.in"},
    {"name": "Rolla Manjula", "email": "manjula.r-29@scds.saiuniversity.edu.in"},
    {"name": "Devireddy Maheswari", "email": "maheswari.d-29@scds.saiuniversity.edu.in"},
    {"name": "Paturu Jeevan Krishna Kishore", "email": "krishnakishore.p-29@scds.saiuniversity.edu.in"},
    {"name": "Peram Tejas", "email": "tejas.p-29@scds.saiuniversity.edu.in"},
    {"name": "Gubala venkata sree teja", "email": "venkatasreeteja.g-29@scds.saiuniversity.edu.in"},
    {"name": "Shaik Safivulla", "email": "safivulla.s-29@scds.saiuniversity.edu.in"},
    {"name": "Anamalagundam Greeshma", "email": "greeshma.a-29@scds.saiuniversity.edu.in"},
    {"name": "Anamalagundam Jaswanth", "email": "jaswanth.a-29@scds.saiuniversity.edu.in"},
    {"name": "Nafeesa Zainul", "email": "zainul.n-29@scds.saiuniversity.edu.in"},
    {"name": "Bellamkonda Greeshma", "email": "greeshma.b-29@scds.saiuniversity.edu.in"},
    {"name": "Pathangi Mokshagna Rao", "email": "mokshagna.p-29@scds.saiuniversity.edu.in"},
    {"name": "Burra Sreenivas", "email": "sreenivas.b-29@scds.saiuniversity.edu.in"},
    {"name": "Morilla Reddy Mahesh Reddy", "email": "maheshreddy.m-29@scds.saiuniversity.edu.in"},
    {"name": "Kottam Sravan Gowtham", "email": "sravangowtham.k-29@scds.saiuniversity.edu.in"},
    {"name": "Savuturi Samuel Daniel", "email": "samueldaniel.s-29@scds.saiuniversity.edu.in"},
    {"name": "Kilari Thanu Sree", "email": "thanusree.k-29@scds.saiuniversity.edu.in"},
    {"name": "Amruta Kandaswamy", "email": "amruta.k-29@scds.saiuniversity.edu.in"}
]

SECTION_2_STUDENTS = [
    ("Moravineni Jishnu Teja", "jishnuteja.m-29@scds.saiuniversity.edu.in"),
    ("Oreddy Sai Praharsa Reddy", "praharsareddy.o-29@scds.saiuniversity.edu.in"),
    ("Kadiveti Nivas", "nivas.k-29@scds.saiuniversity.edu.in"),
    ("Rachuri Harsha Vardhan", "harshavardhan.r-29@scds.saiuniversity.edu.in"),
    ("Polisetty Venkata Surya Jathin", "venkatasuryajathin.p-29@scds.saiuniversity.edu.in"),
    ("Seepareddy Amarnath Reddy", "amarnathreddy.s-29@scds.saiuniversity.edu.in"),
    ("Dirisala Sai Venkata Kartheek", "saivenkatakartheek.d-29@scds.saiuniversity.edu.in"),
    ("Shaik Sadhik", "sadhik.s-29@scds.saiuniversity.edu.in"),
    ("Sakam Mokshitha Reddy", "mokshithareddy.s-29@scds.saiuniversity.edu.in"),
    ("Gampanapalli Karthik", "karthik.g-29@scds.saiuniversity.edu.in"),
    ("Gadipudi Pranathi", "pranathi.g-29@scds.saiuniversity.edu.in"),
    ("Cheppali Ummar Farook", "ummarfarook.c-29@scds.saiuniversity.edu.in"),
    ("Pudota Akhil", "akhil.p-29@scds.saiuniversity.edu.in"),
    ("Vulli Geeta", "geetha.v-29@scds.saiuniversity.edu.in"),
    ("Chaganti Avinash", "avinash.c-29@scds.saiuniversity.edu.in"),
    ("Dasam Sai Sadhvik", "saisadhvik.d-29@scds.saiuniversity.edu.in"),
    ("Dandu Mohith Varma", "mohithvarma.d-29@scds.saiuniversity.edu.in"),
    ("Marrikanti Venkata Dhanush", "venkatadhanush.m-29@scds.saiuniversity.edu.in"),
    ("Angina Pradeep Kumar", "pradeepkumar.a-29@scds.saiuniversity.edu.in"),
    ("Velpula Sai Sravan", "saisravan.v-29@scds.saiuniversity.edu.in"),
    ("Marrigunta Sai Charan", "saicharan.m-29@scds.saiuniversity.edu.in"),
    ("Boddu Mani Sampreeth Reddy", "manisampreeth.b-29@scds.saiuniversity.edu.in"),
    ("Maniswar Reddy Boddu", "maniswarreddy.b-29@scds.saiuniversity.edu.in"),
    ("Bodi Hari Babu", "bodihari.b-29@scds.saiuniversity.edu.in"),
    ("Chandra Padmaja", "padmaja.c-29@scds.saiuniversity.edu.in"),
    ("Shaik Khaja Nawaz", "khajanawaz.s-29@scds.saiuniversity.edu.in"),
    ("Shaik Rushma", "rushma.s-29@scds.saiuniversity.edu.in"),
    ("Gangavarapu Pradeep", "pradeep.g-29@scds.saiuniversity.edu.in"),
    ("Rithul S", "rithul.s-29@scds.saiuniversity.edu.in"),
    ("Rudraraju Srikar Siva Phani Padmaraju", "srikarsivaphanipadmaraju.r-29@scds.saiuniversity.edu.in"),
    ("Besta Manasa Udayini", "manasaudayini.b-29@scds.saiuniversity.edu.in"),
    ("Yarramasetti Sai Eswar", "saieswar.y-29@scds.saiuniversity.edu.in"),
    ("Bommanahal Jaswanth Chowdary", "jaswanth.b-29@scds.saiuniversity.edu.in"),
    ("Madala Gopi Chandu", "gopichandu.m-29@scds.saiuniversity.edu.in"),
    ("Vajrala Spandana", "spandana.v-29@scds.saiuniversity.edu.in"),
    ("Pemmasani Dheeraj", "dheeraj.p-29@scds.saiuniversity.edu.in"),
    ("Gundala Venkata Himesh", "venkathimesh.g-29@scds.saiuniversity.edu.in"),
    ("Pemmasani Eswaradesh", "eswardesh.p-29@scds.saiuniversity.edu.in"),
    ("Kommi Harshith", "harshith.k-29@scds.saiuniversity.edu.in"),
    ("Tumu Indra Reddy", "indrareddy.t-29@scds.saiuniversity.edu.in"),
    ("Maddela Nanda Kishore", "nandakishore.m-29@scds.saiuniversity.edu.in"),
    ("Bommaka Harshitha", "harshitha.b-29@scds.saiuniversity.edu.in"),
    ("Pagadala Venkata Prabhu Likith", "prabhulikith.p-29@scds.saiuniversity.edu.in"),
    ("Bombothula Mohan Vamsi Yadav", "mohanvamsiyadav.b-29@scds.saiuniversity.edu.in"),
    ("Turupusima Chavva Harshitha Reddy", "harshithareddy.t-29@scds.saiuniversity.edu.in"),
    ("Sandrapalli Jahnavi", "jahnavi.s-29@scds.saiuniversity.edu.in"),
    ("Banu Prakash Ramapuram", "prakash.b-29@scds.saiuniversity.edu.in"),
    ("Garikipati Akshaya", "akshaya.g-29@scds.saiuniversity.edu.in"),
    ("Chaganti Chennakesava Srikar Reddy", "srikarreddy.c-29@scds.saiuniversity.edu.in"),
    ("Thota Thrishika", "thrishika.t-29@scds.saiuniversity.edu.in"),
    ("Chemudugunta Thanush", "thanush.c-29@scds.saiuniversity.edu.in"),
    ("Balasamudram Sai Charan", "saicharan.b-29@scds.saiuniversity.edu.in"),
    ("Oggu Madhu Priya", "madhupriya.o-29@scds.saiuniversity.edu.in"),
    ("Baddam Ranjith Reddy", "ranjithreddy.b-29@scds.saiuniversity.edu.in"),
    ("Dudekula Thanveer", "thanveer.d-29@scds.saiuniversity.edu.in"),
    ("Dhanyasi Sandesh Joyal", "sandeshjoyal.d-29@scds.saiuniversity.edu.in"),
    ("Maramreddy Sulakshan Reddy", "sulakshanreddy.m-29@scds.saiuniversity.edu.in"),
    ("Singari Dinesh", "dinesh.s-29@scds.saiuniversity.edu.in"),
    ("Yeduru Lavanya", "lavanya.y-29@scds.saiuniversity.edu.in"),
    ("Gutti Jitendra Pavan", "jitendrapavan.g-29@scds.saiuniversity.edu.in"),
    ("Budhala Pardeep", "pardeep.b-29@scds.saiuniversity.edu.in"),
    ("Yeturi Rakesh", "rakesh.y-29@scds.saiuniversity.edu.in"),
    ("Zaahin Bhattacharyya", "zaahin.b-29@scds.saiuniversity.edu.in"),
    ("Pera Charan Kumar Reddy", "charankumarreddy.p-29@scds.saiuniversity.edu.in"),
    ("Padarthi Mohan Shabariash", "mohansabarish.p-29@scds.saiuniversity.edu.in"),
    ("Pikkili Dharma Sai Kumar", "dharmasaikumar.p-29@scds.saiuniversity.edu.in"),
    ("Pasupuleti Mognesh", "mognesh.p-29@scds.saiuniversity.edu.in"),
    ("Chenna Reddy Gari Manoj Reddy", "garimanojreddy.c-29@scds.saiuniversity.edu.in"),
    ("Unnam Manmohan", "manmohan.u-29@scds.saiuniversity.edu.in"),
    ("Edamalakandi Chaturved", "chaturved.e-29@scds.saiuniversity.edu.in"),
    ("Eswar Sangeetha", "sangeetha.e-29@scds.saiuniversity.edu.in"),
    ("Pagadala Riddhima", "ruddhima.p-29@scds.saiuniversity.edu.in"),
    ("Singamala Santhosh Reddy", "santhoshreddy.s-29@scds.saiuniversity.edu.in"),
    ("Koncha Venkata Ravi Teja Reddy", "ravitejareddy.k-29@scds.saiuniversity.edu.in"),
    ("Koncha Pradeep", "pradeep.k-29@scds.saiuniversity.edu.in"),
    ("Iska Sri Charan", "sricharan.i-29@scds.saiuniversity.edu.in"),
    ("Sai Manikanta Vinay Malireddy", "manikantavinay.s-29@scds.saiuniversity.edu.in"),
    ("Jana Phani Kumar", "phanikumar.j-29@scds.saiuniversity.edu.in"),
    ("Gangisetti Vikas Sri Raj", "vikassriraj.g-29@scds.saiuniversity.edu.in"),
    ("Gangisetti Hemanth Sai Krishna", "hemanthsai.g-29@scds.saiuniversity.edu.in"),
    ("Maddirla Manoj Kumar Reddy", "manojkumarreddy.m-29@scds.saiuniversity.edu.in"),
    ("Alahari Venkata Sai Santhosh", "saisanthosh.a-29@scds.saiuniversity.edu.in"),
    ("Mullagoori Arjun", "arjun.m-29@scds.saiuniversity.edu.in"),
    ("Lukkani Deepak", "deepak.l-29@scds.saiuniversity.edu.in"),
    ("Patnam Manas Tej", "manastej.p-29@scds.saiuniversity.edu.in")
]

SECTION_3_STUDENTS = [
    ("Gangapurapu Jai Charan",              "jaicharan.g-29@scds.saiuniversity.edu.in"),
    ("Payyavula Shashank",                   "shashank.p-29@scds.saiuniversity.edu.in"),
    ("Dondati Pradeep",                      "pradeep.d-29@scds.saiuniversity.edu.in"),
    ("G Yoshithaa Sree",                     "yoshithaasree.g-29@scds.saiuniversity.edu.in"),
    ("Konapalli Poojitha",                   "poojitha.k-29@scds.saiuniversity.edu.in"),
    ("Mandem Sai Vani",                      "saivani.m-29@scds.saiuniversity.edu.in"),
    ("Thirividhi Jaswanth",                  "jaswanth.t-29@scds.saiuniversity.edu.in"),
    ("Chennuru Veera Manjunatha Reddy",      "manjunathareddy.c-29@scds.saiuniversity.edu.in"),
    ("Kajjayam Sai Mourya",                  "saimourya.k-29@scds.saiuniversity.edu.in"),
    ("Mekala Navya Sri",                     "navyasri.m-29@scds.saiuniversity.edu.in"),
    ("Kattamreddy Lakshmi Chaitra",          "lakshmichaitra.k-29@scds.saiuniversity.edu.in"),
    ("Chanduluru Sanhitha Yadav",            "sanhithayadav.c-29@scds.saiuniversity.edu.in"),
    ("Malli Divya",                          "divya.m-29@scds.saiuniversity.edu.in"),
    ("Dondati Pavitra",                      "pavitra.d-29@scds.saiuniversity.edu.in"),
    ("Ramireddy Siva Likitha Reddy",         "sivalikitha.r-29@scds.saiuniversity.edu.in"),
    ("Udatha Sri Vennela",                   "srivennela.u-29@scds.saiuniversity.edu.in"),
    ("Vagathuri Bhargava",                   "bhargava.v-29@scds.saiuniversity.edu.in"),
    ("Valapalli Ram Teja",                   "ramteja.v-29@scds.saiuniversity.edu.in"),
    ("Kamireddy Yoshith Reddy",              "yoshithreddy.k-29@scds.saiuniversity.edu.in"),
    ("Peddireddy Sai Darshan Reddy",         "saidarshanreddy.p-29@scds.saiuniversity.edu.in"),
    ("Innamuri Venkata Sai Lohith",          "venkatasai.i-29@scds.saiuniversity.edu.in"),
    ("Myla Pavan",                           "pavan.m-29@scds.saiuniversity.edu.in"),
    ("Duvvuru Deepak Reddy",                 "deepakreddy.d-29@scds.saiuniversity.edu.in"),
    ("P Tharun",                             "tharun.p-29@scds.saiuniversity.edu.in"),
    ("Pramidhala Hemanth",                   "hemanth.p-29@scds.saiuniversity.edu.in"),
    ("Marri Bhanu Sri",                      "bhanusri.m-29@scds.saiuniversity.edu.in"),
    ("Yelluri Harshavardhan Reddy",          "harshavardhanreddy.y-29@scds.saiuniversity.edu.in"),
    ("Rachavelpula Puneeth Sai",             "puneethsai.r-29@scds.saiuniversity.edu.in"),
    ("Siginam Sai Sathwik",                  "saisathwik.s-29@scds.saiuniversity.edu.in"),
    ("Palacharla Vamsi Krishna",             "vamsikrishna.p-29@scds.saiuniversity.edu.in"),
    ("Amarthaluru Bhavesh",                  "bhavesh.a-29@scds.saiuniversity.edu.in"),
    ("Telaganeni Lohith Manish",             "lohithmanish.t-29@scds.saiuniversity.edu.in"),
    ("Bangarugari Prathyush",                "prathyush.b-29@scds.saiuniversity.edu.in"),
    ("Mahasamudhram Girish Reddy",           "girishreddy.m-29@scds.saiuniversity.edu.in"),
    ("Golla Siva Tharun",                    "sivatharun.g-29@scds.saiuniversity.edu.in"),
    ("Manupati Poorna Chandra",              "poornaachandra.m-29@scds.saiuniversity.edu.in"),
    ("Rathinakumar S",                       "rathinakumar.s-29@scds.saiuniversity.edu.in"),
    ("Godduvelagala Chennakesava",           "chennakesava.g-29@scds.saiuniversity.edu.in"),
    ("Advait D",                             "advait.d-29@scds.saiuniversity.edu.in"),
    ("Yelchuri Ganesh",                      "ganesh.y-29@scds.saiuniversity.edu.in"),
    ("Dondlapadu Ramya Sree",                "ramyasree.d-29@scds.saiuniversity.edu.in"),
    ("Panyam Venkata Gyana Deepak",          "gyanadeepak.p-29@scds.saiuniversity.edu.in"),
    ("Ilupuru Padmajahnavi",                 "padmajahnavi.i-29@scds.saiuniversity.edu.in"),
    ("Malchi Sneha Sruthi",                  "snehasruthi.m-29@scds.saiuniversity.edu.in"),
    ("Devarinti Suma Sri",                   "sumasri.d-29@scds.saiuniversity.edu.in"),
    ("Badhvel Hansika Srinidhi",             "hansikasrinidhi.b-29@scds.saiuniversity.edu.in"),
    ("Pichika V Vyshnavi",                   "vyshnavi.p-29@scds.saiuniversity.edu.in"),
    ("Kannikapuram Teja",                    "teja.k-29@scds.saiuniversity.edu.in"),
    ("Chinka Sumanth",                       "sumanth.c-29@scds.saiuniversity.edu.in"),
    ("Arkadu Mokshitha",                     "mokshitha.a-29@scds.saiuniversity.edu.in"),
    ("Gajji Bhargavi",                       "bhargavi.g-29@scds.saiuniversity.edu.in"),
    ("Chagam Riteeswar Reddy",               "riteeswar.c-29@scds.saiuniversity.edu.in"),
    ("Kotagasti Taheer",                     "thaheer.k-29@scds.saiuniversity.edu.in"),
    ("Peravali Puvan Venkata Pavan",         "venkatapavan.p-29@scds.saiuniversity.edu.in"),
    ("Bathula Hanuma Kotireddy",             "hanumakotireddy.b-29@scds.saiuniversity.edu.in"),
    ("Yenneti Gowtham Sri Sai Srinivasa Murthy", "gowthamsri.y-29@scds.saiuniversity.edu.in"),
    ("Ramireddy Bhavadeep Reddy",            "bhavadeepreddy.r-29@scds.saiuniversity.edu.in"),
    ("Palisetti Harsha Deepika",             "deepikaharsha.p-29@scds.saiuniversity.edu.in"),
    ("Purini Tejeswar",                      "tejeswar.p-29@scds.saiuniversity.edu.in"),
    ("Nagireddy Naveen",                     "naveen.n-29@scds.saiuniversity.edu.in"),
    ("Vunnam Kowshik",                       "kowshik.v-29@scds.saiuniversity.edu.in"),
    ("Palleboyina Vamsi Krishna",            "vamsikrishna.pl-29@scds.saiuniversity.edu.in"),
    ("Venna Bhuvaneshwar",                   "bhuvaneshwar.v-29@scds.saiuniversity.edu.in"),
    ("Kilari Hithesh",                       "kilari.h-29@scds.saiuniversity.edu.in"),
    ("Boddu Vamsidhar Reddy",                "vamsidharreddy.b-29@scds.saiuniversity.edu.in"),
    ("Anbuchelvan V",                        "anbuchelvan.v-29@scds.saiuniversity.edu.in"),
    ("B Vaibhav",                            "vaibhav.b-29@scds.saiuniversity.edu.in"),
    ("S T Suneethra",                        "suneethra.s-29@scds.saiuniversity.edu.in"),
    ("Kolamasanapalli Manjunath",            "manjunath.k-29@scds.saiuniversity.edu.in"),
    ("Dhanemkula Veera Bhargav",             "veerabhargav.d-29@scds.saiuniversity.edu.in"),
    ("Ontimitta Keerthana",                  "keerthana.o-29@scds.saiuniversity.edu.in"),
    ("Koneru Haneeth",                       "haneeth.k-29@scds.saiuniversity.edu.in"),
    ("Golla Shiva Santhosh Reddy",           "shivasanthoshreddy.g-29@scds.saiuniversity.edu.in"),
    ("Vudata Sri Madhavan",                  "srimadhavan.v-29@scds.saiuniversity.edu.in"),
    # Rows 75-85 are Lab Group 8
    ("Dudi Venkata Krishna Karthik",         "venkatakrishnakarthik.d-29@scds.saiuniversity.edu.in"),
    ("Thati Sushmanth Reddy",                "sushmanthreddy.t-29@scds.saiuniversity.edu.in"),
    ("Mallela Mohammad Aqib",                "mohammadaqib.m-29@scds.saiuniversity.edu.in"),
    ("M Arun Kumar",                         "arunkumar.m-29@scds.saiuniversity.edu.in"),
    ("Dasari Venkata Yeswanth",              "venkatayaswanth.d-29@scds.saiuniversity.edu.in"),
    ("Boddu Chiranjeevi",                    "chiranjeevi.b-29@scds.saiuniversity.edu.in"),
    ("Gurram Mahesh",                        "mahesh.g-29@scds.saiuniversity.edu.in"),
    ("Ganugapenta Naga Mahesh",              "nagamahesh.g-29@scds.saiuniversity.edu.in"),
    ("Beeram Naga Maheswar Reddy",           "maheswar.b-29@scds.saiuniversity.edu.in"),
    ("Ayindla Surya",                        "surya.a-29@scds.saiuniversity.edu.in"),
    ("Narbavee V",                           "narbavee.v-29@scds.saiuniversity.edu.in"),
]

# =====================================================================
# SEED FUNCTIONS
# =====================================================================

def seed_school():
    print("Seeding schools...")
    scds = School(
        name='School of Computing and Data Science',
        code='SCDS',
        domain='scds.saiuniversity.edu.in'
    )
    # Adding global universities if needed
    sas = School(name='School of Arts and Sciences', code='SAS', domain='sas.apex.edu.in')
    sol = School(name='School of Law', code='SOL', domain='sol.apex.edu.in')
    
    db.session.add_all([scds, sas, sol])
    db.session.commit()
    return scds

def seed_staff(school):
    print("Seeding staff...")
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    
    # Global Admin
    admin = User(school_id=None, email='admin@saiuniversity.edu.in',
                 password_hash=pw, role='admin', name='System Admin')
    # Superadmin
    superadmin = User(school_id=None, email='superadmin@saiuniversity.edu.in',
                      password_hash=pw, role='superadmin', name='Super Admin')
    
    # SCDS Staff
    dean = User(school_id=school.id, email='dean@scds.saiuniversity.edu.in',
                password_hash=pw, role='dean', name='Dr. Sarah Dean')
    prof = User(school_id=school.id, email='professor@scds.saiuniversity.edu.in',
                password_hash=pw, role='professor', name='Prof. Nitish Rana')
    assistant = User(school_id=school.id, email='assistant@scds.saiuniversity.edu.in',
                     password_hash=pw, role='assistant_professor', name='Asst. Prof. Alex')
    
    db.session.add_all([admin, superadmin, dean, prof, assistant])
    db.session.commit()
    
    # Add profiles
    db.session.add_all([
        Teacher(user_id=prof.id, department='Computer Science'),
        Teacher(user_id=assistant.id, department='Computer Science')
    ])
    db.session.commit()
    return prof

def seed_section_1(school):
    print("Seeding Section 1 students...")
    sec = Section(school_id=school.id, name='Section 1', code='SCDS-CS-S1', batch_year=2025)
    db.session.add(sec)
    db.session.commit()
    
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    for s_data in SECTION_1_STUDENTS:
        user = User(school_id=school.id, email=s_data['email'],
                    password_hash=pw, role='student', name=s_data['name'], must_change_password=True)
        db.session.add(user)
        db.session.flush()
        
        student = Student(user_id=user.id, section_id=sec.id, enrollment_year=2025, major='Computer Science')
        db.session.add(student)
    db.session.commit()

def seed_section_2(school):
    print("Seeding Section 2 students...")
    sec = Section(school_id=school.id, name='Section 2', code='SCDS-CS-S2', batch_year=2025)
    db.session.add(sec)
    db.session.commit()
    
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    for name, email in SECTION_2_STUDENTS:
        user = User(school_id=school.id, email=email,
                    password_hash=pw, role='student', name=name, must_change_password=True)
        db.session.add(user)
        db.session.flush()
        
        student = Student(user_id=user.id, section_id=sec.id, enrollment_year=2025, major='Computer Science')
        db.session.add(student)
    db.session.commit()

def seed_section_3(school):
    print("Seeding Section 3 students...")
    sec = Section(school_id=school.id, name='Section 3', code='SCDS-CS-S3', batch_year=2025)
    db.session.add(sec)
    db.session.commit()
    
    pw = bcrypt.generate_password_hash('hive@1234').decode('utf-8')
    for i, (name, email) in enumerate(SECTION_3_STUDENTS):
        # Rows 75-85 (indices 74-84) get lab_section=8, others lab_section=3
        lab_sec = 8 if i >= 74 else 3
        
        user = User(school_id=school.id, email=email,
                    password_hash=pw, role='student', name=name, must_change_password=True)
        db.session.add(user)
        db.session.flush()
        
        student = Student(user_id=user.id, section_id=sec.id, enrollment_year=2025, 
                          major='Computer Science', lab_section=lab_sec)
        db.session.add(student)
    db.session.commit()
    return sec

def seed_timetable(school, section_3, teacher_user):
    print("Seeding courses and timetable...")
    
    # Courses for Section 3
    courses_to_create = [
        ("Discrete Mathematics", "CS-301", 4),
        ("Indian Constitution and Democracy", "ICD-101", 2),
        ("Python and Data Structure (LAB)", "CS-302L", 2),
        ("Introduction to Data Structures", "CS-302", 4),
        ("Environment and Sustainability", "ES-101", 2),
        ("Programming in Python", "CS-303", 4),
    ]
    
    section_courses = {}
    for name, code, credits in courses_to_create:
        course = Course(
            section_id=section_3.id,
            name=name,
            code=code,
            teacher_id=teacher_user.id,
            credits=credits
        )
        db.session.add(course)
        db.session.flush()
        section_courses[name] = course

    # Timetable data for Section 3
    entries_data = [
        # Monday
        (0, "10:40 AM", "12:10 PM", "Discrete Mathematics", "AB2 - 203", "#cfe2f3"),
        (0, "02:15 PM", "03:40 PM", "Indian Constitution and Democracy", "AB2 - 202", "#ead1dc"),
        (0, "03:50 PM", "05:15 PM", "Python and Data Structure (LAB)", "Computer Lab - AB1 - First Floor", "#b45f06"),
        # Tuesday
        (1, "09:00 AM", "10:30 AM", "Introduction to Data Structures", "AB1 - 101", "#f9cb9c"),
        (1, "12:15 PM", "01:45 PM", "Environment and Sustainability", "AB1 - Moot Court Hall", "#d9ead3"),
        # Wednesday
        (2, "09:00 AM", "10:30 AM", "Discrete Mathematics", "AB2 - 203", "#cfe2f3"),
        (2, "02:15 PM", "03:40 PM", "Indian Constitution and Democracy", "AB2 - 207", "#ead1dc"),
        # Thursday
        (3, "09:00 AM", "10:30 AM", "Programming in Python", "AB2 - 207", "#fce5cd"),
        (3, "12:20 PM", "01:40 PM", "Python and Data Structure (LAB)", "Computer Lab - AB1 - First Floor", "#b45f06"),
        # Friday
        (4, "10:40 AM", "12:10 PM", "Programming in Python", "AB2 - 202", "#fce5cd"),
        (4, "02:15 PM", "03:40 PM", "Introduction to Data Structures", "AB2 - 202", "#f9cb9c"),
        (4, "03:50 PM", "05:15 PM", "Environment and Sustainability", "AB2 - 202", "#d9ead3"),
    ]

    for day, start, end, title, room, color in entries_data:
        course = section_courses.get(title)
        entry = TimetableEntry(
            section_id=section_3.id,
            course_id=course.id if course else None,
            day=day,
            start_time=start,
            end_time=end,
            title=title,
            teacher=teacher_user.name,
            room=room,
            color=color,
            status='active'
        )
        db.session.add(entry)
    db.session.commit()

def seed_all():
    school = seed_school()
    prof = seed_staff(school)
    seed_section_1(school)
    seed_section_2(school)
    sec3 = seed_section_3(school)
    seed_timetable(school, sec3, prof)
    print("All data seeded successfully.")

if __name__ == "__main__":
    with app.app_context():
        print("Dropping and recreating all tables for a fresh seed...")
        db.metadata.drop_all(bind=db.engine)
        db.create_all()
        seed_all()
        print("Database seeded successfully.")
