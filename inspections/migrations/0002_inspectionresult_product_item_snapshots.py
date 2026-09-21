import django.db.models.deletion
from django.db import migrations, models


def populate_product_items_and_snapshots(apps, schema_editor):
    InspectionResult = apps.get_model("inspections", "InspectionResult")
    ProductInspectionItem = apps.get_model("products", "ProductInspectionItem")

    for result in InspectionResult.objects.select_related("inspection__batch__product", "item").all():
        try:
            product_item = ProductInspectionItem.objects.get(
                product=result.inspection.batch.product,
                item=result.item,
            )
        except ProductInspectionItem.DoesNotExist as exc:
            raise RuntimeError(
                "Cannot migrate inspection result without matching ProductInspectionItem "
                f"(inspection_result_id={result.id}, product_id={result.inspection.batch.product_id}, item_id={result.item_id})."
            ) from exc
        result.product_item = product_item
        result.standard_min_snapshot = result.item.standard_min
        result.standard_max_snapshot = result.item.standard_max
        result.inspection_method_snapshot = result.item.inspection_method
        result.unit_snapshot = result.item.unit
        result.save(
            update_fields=[
                "product_item",
                "standard_min_snapshot",
                "standard_max_snapshot",
                "inspection_method_snapshot",
                "unit_snapshot",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("inspections", "0001_initial"),
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inspectionresult",
            name="product_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="results",
                to="products.productinspectionitem",
            ),
        ),
        migrations.AddField(
            model_name="inspectionresult",
            name="standard_min_snapshot",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="inspectionresult",
            name="standard_max_snapshot",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="inspectionresult",
            name="inspection_method_snapshot",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="inspectionresult",
            name="unit_snapshot",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.RunPython(populate_product_items_and_snapshots, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="inspectionresult",
            name="uq_inspection_item",
        ),
        migrations.AlterField(
            model_name="inspectionresult",
            name="product_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="results",
                to="products.productinspectionitem",
            ),
        ),
        migrations.AddConstraint(
            model_name="inspectionresult",
            constraint=models.UniqueConstraint(fields=("inspection", "product_item"), name="uq_inspection_product_item"),
        ),
        migrations.RemoveField(
            model_name="inspectionresult",
            name="item",
        ),
    ]
