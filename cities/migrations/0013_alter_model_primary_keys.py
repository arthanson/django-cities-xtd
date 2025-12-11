from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cities", "0012_alter_country_neighbours"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alternativename",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="city",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="continent",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="country",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="country",
            name="neighbours",
            field=models.ManyToManyField(to="cities.Country"),
        ),
        migrations.AlterField(
            model_name="district",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="postalcode",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="region",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="subregion",
            name="id",
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
