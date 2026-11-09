# Script tu dong tao file audio tieng Anh thuc te cho 6 bai IELTS Listening
# Su dung bo tong hop giong noi Microsoft Text-To-Speech co san trong Windows

Add-Type -AssemblyName System.Speech

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " DANG TAO FILE AM THANH GIONG DOC TIENG ANH CHO 6 BAI..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$outputDir = Join-Path $PSScriptRoot "media\listening"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0  # Toc do doc chuan (IELTS normal pace)
$synth.Volume = 100

# Chon giong doc tieng Anh neu co san
$englishVoice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq "en" } | Select-Object -First 1
if ($englishVoice) {
    $synth.SelectVoice($englishVoice.VoiceInfo.Name)
    Write-Host "-> Su dung giong doc: $($englishVoice.VoiceInfo.Name)" -ForegroundColor Green
}

# -------------------------------------------------------------
# BAI 1: Student Accommodation and Housing Enquiry
# -------------------------------------------------------------
$file1 = Join-Path $outputDir "audio_exercise_1.wav"
Write-Host "1. Dang tao audio Bai 1: $file1..." -ForegroundColor Yellow
$script1 = @"
Narrator: You will hear a conversation between an international student, Alex, and a university housing officer, Mrs. Davis.

Mrs. Davis: Good morning, welcome to the Student Accommodation Services. How can I help you today?
Alex: Hello! I am an incoming first-year student, and I am looking for a place to stay near campus.
Mrs. Davis: Wonderful! For first-year international students, we strongly recommend our University Residence Halls. They are secure, close to lecture theatres, and provide a great community atmosphere.
Alex: That sounds ideal. What about the pricing?
Mrs. Davis: Standard rooms range from 400 to 500 dollars a month. What is your budget?
Alex: My maximum monthly budget is 450 dollars, ideally including utility bills.
Mrs. Davis: That fits nicely with our Hall B option. Standard water and heating are included in this package. To secure your reservation, you must submit a scanned copy of your Student ID card before next Friday.
Alex: Perfect, I will email the copy this afternoon. Thank you very much!
"@
$synth.SetOutputToWaveFile($file1)
$synth.Speak($script1)

# -------------------------------------------------------------
# BAI 2: City Leisure Centre Registration & Facilities
# -------------------------------------------------------------
$file2 = Join-Path $outputDir "audio_exercise_2.wav"
Write-Host "2. Dang tao audio Bai 2: $file2..." -ForegroundColor Yellow
$script2 = @"
Narrator: You will hear a customer service representative explaining leisure centre facilities and membership terms.

Officer: Good afternoon! Welcome to Riverdale Community Sports Centre.
Customer: Hi, I would like some information about joining the sports centre.
Officer: Certainly! Our facilities include a gym, fitness studios, and an Olympic-sized swimming pool. On weekdays, the swimming pool opens early at 6:00 AM for morning lap swimmers.
Customer: That is great for my schedule. How much is the membership?
Officer: A standard adult membership is 250 pounds, but if you have a valid student card, an annual student pass is discounted to only 180 pounds per year.
Customer: Excellent. Are fitness classes included?
Officer: Most classes like yoga and aerobics are drop-in, but our indoor cycling spin class requires advance booking at least 24 hours ahead due to limited bikes.
Customer: Understood. What about the changing room lockers and indoor court shoes?
Officer: Lockers use a returnable one-pound coin deposit, so you get your money back. And please remember that in the badminton courts, members must wear clean sports shoes with non-marking rubber soles.
"@
$synth.SetOutputToWaveFile($file2)
$synth.Speak($script2)

# -------------------------------------------------------------
# BAI 3: University Library Orientation and Research Services
# -------------------------------------------------------------
$file3 = Join-Path $outputDir "audio_exercise_3.wav"
Write-Host "3. Dang tao audio Bai 3: $file3..." -ForegroundColor Yellow
$script3 = @"
Narrator: Welcome to the University Central Library Orientation Tour. Please listen carefully as we guide you through our research facilities.

Librarian: Good afternoon, everyone! On the Ground Floor, you will find our main circulation desk, self-service borrowing machines, and the general computer lab with high-speed printing.
Moving up to the Second Floor, we host our main book collection and collaborative group study rooms.
However, if you require absolute quiet for concentration, please head up to the Third Floor. Level 3 is reserved strictly for silent research and individual study pods.
Regarding borrowing allowances: undergraduate students may borrow up to 10 items, whereas postgraduate researchers are entitled to borrow up to 15 books simultaneously for a duration of four weeks.
Finally, please note that our interlibrary loan service with partner institutions across the country is completely free of charge for all enrolled students.
Thank you, and happy researching!
"@
$synth.SetOutputToWaveFile($file3)
$synth.Speak($script3)

# -------------------------------------------------------------
# BAI 4: Sustainable Urban Transport Planning Interview
# -------------------------------------------------------------
$file4 = Join-Path $outputDir "audio_exercise_4.wav"
Write-Host "4. Dang tao audio Bai 4: $file4..." -ForegroundColor Yellow
$script4 = @"
Narrator: You will hear a radio interview with Dr. Marcus Vance, a municipal urban transport planner.

Interviewer: Dr. Vance, your team recently published an evaluation of the city's green mobility policy. What were the most noticeable results?
Dr. Vance: The headline outcome was that two years after introducing the inner-city congestion charge, passenger vehicle traffic in the central district dropped by 24 percent.
Interviewer: That is a substantial decrease. What is replacing those private car trips?
Dr. Vance: Primarily public transit and cycling. To support this, the city council has committed to electrifying our entire municipal bus fleet by the year 2030.
Interviewer: And how do commuters navigate between different transit modes?
Dr. Vance: We constructed new multimodal transit interchanges. These hubs provide seamless, sheltered connections between trams, city buses, and secured bicycle parking. Furthermore, commuters no longer need paper tickets; our universal contactless payment system allows tapping with any smartphone or debit card.
"@
$synth.SetOutputToWaveFile($file4)
$synth.Speak($script4)

# -------------------------------------------------------------
# BAI 5: Marine Ecosystem Lecture: Coral Bleaching Mechanisms
# -------------------------------------------------------------
$file5 = Join-Path $outputDir "audio_exercise_5.wav"
Write-Host "5. Dang tao audio Bai 5: $file5..." -ForegroundColor Yellow
$script5 = @"
Narrator: You will hear part of a lecture on marine ecology and environmental change.

Lecturer: Good morning, students. Today we examine the delicate symbiotic relationship that forms the backbone of coral reef ecosystems.
Reef-building corals rely heavily on microscopic photosynthetic algae called zooxanthellae living within their tissues.
Under normal conditions, these algae supply up to 90 percent of the coral host's nutritional energy requirements through photosynthesis.
However, this partnership is highly vulnerable to thermal anomalies. When sea surface temperatures rise even one or two degrees Celsius above historical summer averages, the coral experiences thermal stress.
In response, the coral expels the zooxanthellae. Because coral tissue is naturally translucent, shedding the pigmented algae exposes the stark white calcium carbonate skeleton beneath—a process known as coral bleaching.
Crucially, bleaching is not an instantaneous death sentence. If ambient water temperatures return to baseline within several weeks, bleached corals can reabsorb symbiotic microalgae and make a full recovery.
"@
$synth.SetOutputToWaveFile($file5)
$synth.Speak($script5)

# -------------------------------------------------------------
# BAI 6: Archaeological Symposium: Aerial LiDAR Technology
# -------------------------------------------------------------
$file6 = Join-Path $outputDir "audio_exercise_6.wav"
Write-Host "6. Dang tao audio Bai 6: $file6..." -ForegroundColor Yellow
$script6 = @"
Narrator: You will hear an archaeologist delivering a keynote presentation on modern remote sensing techniques.

Speaker: Good morning, colleagues. Over the past decade, aerial LiDAR—which stands for Light Detection and Ranging—has utterly transformed Mesoamerican archaeology.
Historically, ancient structures beneath thick rainforest canopies required arduous ground expeditions. Airborne LiDAR overcomes this by firing hundreds of thousands of laser pulses per second from an aircraft. While the majority bounce off the foliage, enough photons filter through gaps in the leaves to measure ground topography.
Specialized computer algorithms then strip away the vegetation returns to generate a digital bare-earth terrain model.
When we applied this in northern Guatemala, the findings overturned decades of scholarly assumptions. Instead of isolated jungle settlements, LiDAR revealed massive interconnected urban networks. Most impressively, we discovered vast networks of terraced agricultural hillsides and sophisticated irrigation canals, proving that ancient populations sustained complex farming at an unprecedented scale.
"@
$synth.SetOutputToWaveFile($file6)
$synth.Speak($script6)

$synth.Dispose()

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " HOAN THANH! Toan bo 6 file audio da duoc cap nhat vao media\listening\" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
