# Generated manually for system category and posts

from django.db import migrations, models


def create_system_category_and_posts(apps, schema_editor):
    PostCategory = apps.get_model('board', 'PostCategory')
    Post = apps.get_model('board', 'Post')

    # Create or get System category
    system_category, created = PostCategory.objects.get_or_create(
        name='System',
        defaults={
            'priority': 900
        }
    )

    # Define system posts to create/update
    system_posts_data = [
        {
            'title': 'Start',
            'text': 'Witaj na Wikikracji! To jest strona startowa.',
            'subtitle': 'Strona startowa',
            'system_key': 'start'
        },
        {
            'title': 'Footer',
            'text': 'To jest stopka strony.',
            'subtitle': 'Stopka',
            'system_key': 'footer'
        },
        {
            'title': 'Welcome E-mail after user was accepted',
            'text': '''Welcome {username}<br><br>Your account on {host} is now active<br><br>Login: {email}<br>Password: {password}<br><br>You may login here: {login_url}<br><br>You may change password here: {password_url}''',
            'subtitle': 'E-mail powitalny po przyjęciu do grupy',
            'system_key': 'welcome_email'
        }
    ]

    for post_data in system_posts_data:
        title = post_data['title']
        system_key = post_data['system_key']
        
        # Check if post already exists by system_key (preferred) or title (fallback)
        existing_post = Post.objects.filter(system_key=system_key).first()
        if not existing_post:
            existing_post = Post.objects.filter(title__iexact=title).first()
        
        if existing_post:
            # Update existing post
            existing_post.category = system_category
            existing_post.is_public = False
            existing_post.system_key = system_key
            existing_post.save()
        else:
            # Create new post
            Post.objects.create(
                title=title,
                text=post_data['text'],
                subtitle=post_data.get('subtitle', ''),
                category=system_category,
                is_public=False,
                author=None,
                system_key=system_key
            )


def reverse_system_category_and_posts(apps, schema_editor):
    PostCategory = apps.get_model('board', 'PostCategory')
    Post = apps.get_model('board', 'Post')

    # Remove System category and its posts
    system_category = PostCategory.objects.filter(name='System').first()
    if system_category:
        # Delete posts in System category (bypass validation for system posts)
        Post.objects.filter(category=system_category).delete()
        # Delete the category
        system_category.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0008_post_featured_image_postattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='system_key',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='System Key'),
        ),
        migrations.RunPython(create_system_category_and_posts, reverse_system_category_and_posts),
    ]
