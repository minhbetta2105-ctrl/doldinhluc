"""Seed original practice Speaking exercises without touching existing user content.

Course project: IELTS practice only, not actual copyrighted exam questions.
Run: python manage.py seed_speaking_demo
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from speaking.models import SpeakingExercise, SpeakingSupport

# [Title, part, topic, level, question, idea, sample, useful vocabulary]
SAMPLES = [
    (
        'Everyday Routine and Weekends', 'PART_1', 'Daily Life', 'BEGINNER',
        'What time do you usually start your day? How do you travel to school or work? How do you normally spend your weekends?',
        'Answer each question separately. Mention your usual time, give one reason and share a real example. Aim for natural, short answers.',
        'I usually wake up at about six thirty. After breakfast, I take the bus to university because it is convenient and affordable. On weekends, I often meet friends or read at home, which helps me recharge.',
        'daily routine; commute; convenient; affordable; recharge; on weekends',
    ),
    (
        'Your Hometown', 'PART_1', 'Hometown', 'BEGINNER',
        'Where is your hometown? What do you like most about living there? Has your hometown changed in recent years?',
        'Identify your hometown, describe a specific feature and compare the past with the present.',
        'I come from a medium-sized city in central Vietnam. I love its relaxed atmosphere and friendly people. In recent years there have been more cafés and public spaces, but the city still feels welcoming.',
        'hometown; atmosphere; welcoming; local community; public spaces; develop',
    ),
    (
        'Studies and Future Plans', 'PART_1', 'Education', 'BEGINNER',
        'What subject are you studying? Why did you choose it? How do you think it will help your future career?',
        'Name a subject, explain your motivation, then link one skill to a possible job.',
        'I study information systems because I enjoy solving practical problems with technology. I particularly like designing websites. I hope the course will help me work in a digital business in the future.',
        'major; practical skills; career path; motivated; technology; solve problems',
    ),
    (
        'A Useful Electronic Device', 'PART_2', 'Technology', 'INTERMEDIATE',
        'Describe an electronic device that you find useful. You should say: what it is; when or how you got it; what you use it for; and explain why it is important to you.',
        'Structure a 1–2 minute response: introduce the device, tell its story, explain two uses and end with personal significance.',
        'I would like to talk about my digital watch, which I received as a gift from my family. I use it to check the time, set reminders and stay organised during busy school days. It was not very expensive, but it means a lot to me because it reminds me of their support. It is also comfortable to wear and fits my wrist perfectly.',
        'practical; receive as a gift; reminders; stay organised; comfortable; meaningful',
    ),
    (
        'A Memorable Journey', 'PART_2', 'Travel', 'INTERMEDIATE',
        'Describe a journey you remember well. You should say: where you went; whom you travelled with; what you did; and explain what made the journey memorable.',
        'Tell a real story with setting, activities, a memorable moment and a concluding feeling.',
        'Last summer, I travelled to a coastal town with a few friends. We explored the local market, tried regional food and watched the sunset by the sea. The trip was memorable because we had time to talk and enjoy simple moments away from our usual routines.',
        'journey; coastal town; explore; local cuisine; memorable; routine',
    ),
    (
        'Someone Who Helped You Learn', 'PART_2', 'People', 'INTERMEDIATE',
        'Describe a person who helped you learn something important. You should say: who the person is; what they taught you; how they helped; and explain why you are grateful.',
        "Give one concrete example of the person's advice and explain the change it brought to you.",
        'One of my classmates helped me learn to speak English with more confidence. We practised short conversations every evening and corrected each other gently. I am grateful because I no longer feel so nervous when speaking in front of others.',
        'supportive; encouragement; confidence; practise; patient; grateful',
    ),
    (
        'Technology in Education', 'PART_3', 'Education', 'ADVANCED',
        'How has technology changed the way people learn? What are the advantages and disadvantages of online learning? Should schools limit smartphone use?',
        'Discuss both sides, use examples and distinguish the needs of different age groups.',
        'Technology makes learning resources easier to access and allows students to study at their own pace. However, online courses demand self-discipline, and smartphones can distract learners. In my view, schools should teach responsible use rather than impose a complete ban.',
        'accessibility; self-discipline; distraction; responsible use; learning outcomes; digital skills',
    ),
    (
        'Cities and Public Transport', 'PART_3', 'Urban Life', 'ADVANCED',
        'Why do some cities struggle with traffic congestion? What could governments do to encourage public transport? Will people use fewer private cars in the future?',
        'Compare public and private transport; consider cost, convenience and long-term policy.',
        'Congestion is often caused by rapid urban growth and limited transport infrastructure. Reliable buses and better pedestrian connections could reduce private car use. However, these changes take sustained investment and public trust.',
        'congestion; infrastructure; reliability; investment; pedestrian; sustainable transport',
    ),
    (
        'Protecting the Environment', 'PART_3', 'Environment', 'ADVANCED',
        'What environmental issues affect your community? Who should take more responsibility, individuals or governments? How can young people contribute?',
        'Present a balanced argument; suggest one realistic action for the community and one at policy level.',
        'Plastic waste and air pollution are major concerns in many communities. Individuals can reduce waste, but governments are in a stronger position to improve infrastructure and enforce standards. Young people can organise awareness campaigns and model better habits.',
        'environmental impact; responsibility; enforce standards; awareness; recycling; community action',
    ),
]

class Command(BaseCommand):
    help = 'Add nine original, published IELTS Speaking practice tasks (idempotent).'

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for title, part, topic, level, prompt, ideas, sample, vocab in SAMPLES:
            obj, created = SpeakingExercise.objects.get_or_create(
                title=title,
                defaults={'part': part, 'topic': topic, 'level': level,
                          'prompt_text': prompt, 'status': SpeakingExercise.Status.PUBLISHED},
            )
            # Never edit existing questions, statuses, scores or learner submissions.
            if created:
                SpeakingSupport.objects.get_or_create(
                    exercise=obj,
                    defaults={'idea_hint': ideas, 'sample_answer': sample,
                              'suggested_vocabulary': vocab},
                )
                created_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Created {created_count} exercises. Total published: '
            f'{SpeakingExercise.objects.filter(status=SpeakingExercise.Status.PUBLISHED).count()}'
        ))
