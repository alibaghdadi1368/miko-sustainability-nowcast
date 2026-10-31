"""ANSI mode: a bad value must fail loudly, never turn into NULL without a trace.

This is the lesson from the Dutch housing project, where pd.to_numeric(errors="coerce")
silently turned 78,112 values with a decimal comma ("1,2") into missing values.
"""

import pytest
from pyspark.sql import functions as F

pytestmark = pytest.mark.spark


def test_plain_cast_of_a_decimal_comma_fails(spark):
    df = spark.createDataFrame([("1,2",)], ["raw"])
    with pytest.raises(Exception, match="CAST_INVALID_INPUT"):
        df.select(F.col("raw").cast("double")).collect()


def test_try_cast_marks_it_as_null_on_purpose(spark):
    df = spark.createDataFrame([("1,2",)], ["raw"])
    value = df.select(F.col("raw").try_cast("double").alias("v")).first()["v"]
    assert value is None


def test_replacing_the_comma_first_gives_the_right_number(spark):
    df = spark.createDataFrame([("1,2",)], ["raw"])
    fixed = df.select(F.regexp_replace("raw", ",", ".").cast("double").alias("v")).first()["v"]
    assert fixed == pytest.approx(1.2)
