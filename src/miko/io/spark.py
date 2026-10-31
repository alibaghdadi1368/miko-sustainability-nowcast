"""One place that builds the Spark session, so every job and test uses the same settings."""

from __future__ import annotations

from pathlib import Path

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

from miko.settings import Settings


def build_spark(
    settings: Settings, app_name: str = "miko", warehouse_dir: Path | None = None
) -> SparkSession:
    """A local Spark session with Delta Lake.

    - ANSI mode on: a bad cast (for example "1,2" to a number) fails loudly instead of
      silently becoming NULL. This is the same default as Spark 4 and Databricks.
    - Time zone UTC: every timestamp means the same moment everywhere.
    """
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.ansi.enabled", "true")
        .config("spark.sql.session.timezone", "UTC")
        .config("spark.driver.memory", settings.spark_driver_memory)
        .config("spark.sql.shuffle.partitions", str(settings.spark_shuffle_partitions))
        .config("spark.ui.showConsoleProgress", "false")
    )
    if warehouse_dir is not None:
        builder = builder.config("spark.sql.warehouse.dir", str(warehouse_dir))

    # Adds the Delta jar (io.delta:delta-spark_2.13:<version>), downloaded once from Maven.
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
