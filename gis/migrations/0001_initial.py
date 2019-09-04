# Generated by Django 2.2.2 on 2019-09-04 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PostalCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=180, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True)),
                ('country_code', models.CharField(blank=True, max_length=2, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('place_name', models.CharField(blank=True, max_length=180, null=True)),
                ('admin_name1', models.CharField(blank=True, max_length=100, null=True)),
                ('admin_code1', models.CharField(blank=True, max_length=20, null=True)),
                ('admin_name2', models.CharField(blank=True, max_length=100, null=True)),
                ('admin_code2', models.CharField(blank=True, max_length=20, null=True)),
                ('admin_name3', models.CharField(blank=True, max_length=100, null=True)),
                ('admin_code3', models.CharField(blank=True, max_length=20, null=True)),
                ('accuracy', models.IntegerField(choices=[(1, 'Estimated'), (4, 'Geoname ID'), (6, 'Centroid of addresses or shape')], null=True)),
                ('updated', models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
