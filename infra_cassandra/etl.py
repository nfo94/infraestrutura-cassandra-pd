import glob
import logging
import os
import uuid

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, first
from pyspark.sql.functions import sum as spark_sum
from pyspark.sql.functions import udf

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_IPEA = os.path.join(BASE_PATH, "raw_data/ipea/*.csv")
RAW_DATA_DADOS_ABERTOS = os.path.join(BASE_PATH, "raw_data/dados_abertos/*.csv")
OUTPUT_DIR = "./data"
OUTPUT_IPEA = os.path.join(OUTPUT_DIR, "people_40_59_by_city_ba.csv")
OUTPUT_DADOS_ABERTOS = os.path.join(OUTPUT_DIR, "people_40_59_covid_d1_by_city_ba.csv")

uuid_udf = udf(lambda: str(uuid.uuid4()))


def read_csv(spark, path, header=True, inferSchema=True):
    return spark.read.csv(path, header=header, inferSchema=inferSchema)


def write_single_csv(df, output_path, temp_dir):
    df.write.csv(temp_dir, header=True, mode="overwrite")
    part_file = glob.glob(os.path.join(temp_dir, "part-*.csv"))[0]
    os.rename(part_file, output_path)


def process_ipea_data(spark):
    df_ipea = read_csv(spark, RAW_DATA_IPEA)
    df_ipea = df_ipea.select(
        col("Município").alias("city_name"),
        col("2022").cast("int"),
    ).withColumn("uuid", uuid_udf())

    result_df_ipea = df_ipea.groupBy("city_name").agg(
        first("uuid").alias("uuid"), spark_sum("2022").alias("population_40_59")
    )
    write_single_csv(result_df_ipea, OUTPUT_IPEA, "people_40_59_by_city_ba")


def process_dados_abertos_data(spark):
    df_dados_abertos = read_csv(spark, RAW_DATA_DADOS_ABERTOS)
    df_dados_abertos = (
        df_dados_abertos.select(
            col("Município").alias("city_name"),
            col("Pessoas 50 a 59 anos - D1").cast("int").alias("people_years_50_59_d1"),
            col("Pessoas 40 a 49 anos - D1").cast("int").alias("people_years_40_49_d1"),
        )
        .withColumn(
            "vaccinated_people_d1_40_59",
            col("people_years_50_59_d1") + col("people_years_40_49_d1"),
        )
        .withColumn("uuid", uuid_udf())
    )

    df_dados_abertos = df_dados_abertos.select(
        "city_name", "vaccinated_people_d1_40_59", "uuid"
    )
    write_single_csv(
        df_dados_abertos, OUTPUT_DADOS_ABERTOS, "people_40_59_covid_d1_by_city_ba"
    )


def etl():
    with SparkSession.builder.appName("analises_covid").getOrCreate() as spark:
        process_ipea_data(spark)
        process_dados_abertos_data(spark)


def main():
    try:
        logging.info("###### Doing ETL on raw data...")
        etl()
    except Exception as e:
        logging.error(f"###### Failed to operate: {e}")


if __name__ == "__main__":
    main()
