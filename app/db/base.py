from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 👇 Agrega este método a cada modelo para forzar el motor
Base.__table_args__ = {'mysql_engine': 'InnoDB'}
