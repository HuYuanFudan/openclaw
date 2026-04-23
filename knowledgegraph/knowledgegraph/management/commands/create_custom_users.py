from django.core.management.base import BaseCommand
from knowledgegraph.models import CustomUser

class Command(BaseCommand):
    help = 'Create custom users'
    def handle(self, *args, **options):
        # 创建 Type 1 用户
        user1 = CustomUser.objects.create_user(username='neo4j', password='neo4j6008', user_type='neo4j')
        # 创建 Type 2 用户
        user2 = CustomUser.objects.create_user(username='metaknowledge', password='metaknowledge6008', user_type='metaknowledge')
        self.stdout.write(self.style.SUCCESS('Successfully created custom users'))