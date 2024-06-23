
import function.randomGacha as gacha
from dotenv import load_dotenv
load_dotenv()

gacha_calculator = gacha.GachaCalculator("database.db", "admin")

bannerName = "World End"
tier = "SR"

item = gacha_calculator.multiple_pulls(bannerName, 10)

for i in range(len(item)):
    print(item[i])
