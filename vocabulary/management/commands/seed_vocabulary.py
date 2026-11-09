"""Nạp dữ liệu mẫu Vocabulary để demo.

Chạy:  python manage.py seed_vocabulary
Chạy nhiều lần vẫn an toàn: không tạo trùng, không xóa dữ liệu bạn đã nhập.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from vocabulary.models import Status, Topic, Word
from vocabulary.seed_data import TOPICS


class Command(BaseCommand):
    help = "Nạp 4 chủ đề từ vựng mẫu (Education, Environment, Technology, Travel)."

    @transaction.atomic
    def handle(self, *args, **options):
        new_topics = new_words = 0
        for t in TOPICS:
            topic, created = Topic.objects.get_or_create(
                name=t["name"],
                defaults={"description": t["description"], "level": t["level"],
                          "status": Status.PUBLISHED},
            )
            new_topics += int(created)
            for word, phonetic, pos, meaning, example, gap, answer in t["words"]:
                _, w_created = Word.objects.get_or_create(
                    topic=topic, word=word,
                    defaults={"phonetic": phonetic, "part_of_speech": pos,
                              "meaning_vi": meaning, "example_sentence": example,
                              "gap_sentence": gap, "gap_answer": answer,
                              "status": Status.PUBLISHED},
                )
                new_words += int(w_created)
        self.stdout.write(self.style.SUCCESS(
            f"Xong: thêm {new_topics} chủ đề mới, {new_words} từ mới "
            f"(tổng {Topic.objects.count()} chủ đề, {Word.objects.count()} từ)."))
