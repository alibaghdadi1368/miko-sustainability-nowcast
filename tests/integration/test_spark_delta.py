"""Hello Delta: the four Delta features this project depends on."""

import pytest
from delta.tables import DeltaTable

pytestmark = pytest.mark.spark


def test_write_and_read_back(spark, tmp_path):
    path = str(tmp_path / "cows")
    spark.createDataFrame([(1, "Bella"), (2, "Daisy")], ["cow_id", "name"]).write.format(
        "delta"
    ).save(path)
    assert spark.read.format("delta").load(path).count() == 2


def test_append_creates_a_new_version_and_time_travel_reads_the_old_one(spark, tmp_path):
    path = str(tmp_path / "milkings")
    spark.createDataFrame([(1, 12.5)], ["cow_id", "milk_kg"]).write.format("delta").save(path)
    spark.createDataFrame([(2, 9.0)], ["cow_id", "milk_kg"]).write.format("delta").mode(
        "append"
    ).save(path)

    assert spark.read.format("delta").load(path).count() == 2
    version_0 = spark.read.format("delta").option("versionAsOf", 0).load(path)
    assert version_0.count() == 1


def test_merge_updates_existing_rows_and_inserts_new_ones(spark, tmp_path):
    path = str(tmp_path / "herd")
    spark.createDataFrame([(1, "milking"), (2, "dry")], ["cow_id", "status"]).write.format(
        "delta"
    ).save(path)
    updates = spark.createDataFrame([(2, "milking"), (3, "heifer")], ["cow_id", "status"])

    (
        DeltaTable.forPath(spark, path)
        .alias("t")
        .merge(updates.alias("u"), "t.cow_id = u.cow_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )

    rows = {r.cow_id: r.status for r in spark.read.format("delta").load(path).collect()}
    assert rows == {1: "milking", 2: "milking", 3: "heifer"}


def test_running_the_same_merge_twice_changes_nothing(spark, tmp_path):
    """Idempotency: the golden rule of every Miko job."""
    path = str(tmp_path / "events")
    spark.createDataFrame([("e1", 10.0)], ["event_id", "milk_kg"]).write.format("delta").save(path)
    batch = spark.createDataFrame([("e1", 10.0), ("e2", 8.0)], ["event_id", "milk_kg"])

    for _ in range(2):
        (
            DeltaTable.forPath(spark, path)
            .alias("t")
            .merge(batch.alias("b"), "t.event_id = b.event_id")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )

    assert spark.read.format("delta").load(path).count() == 2