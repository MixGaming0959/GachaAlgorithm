import function.randomGacha as gacha

userName = "admin"

def main():
    gacha_calculator = gacha.GachaCalculator("database.db", userName)

    available_banners = gacha_calculator.getAvableBanner()
    for i in range(len(available_banners)):
        print("Banner Name: ", available_banners[i]["Name"])
        print("Start Date: ", available_banners[i]["start_date"])
        print("End Date: ", available_banners[i]["end_date"])
        print()


    bannerName = "Mystic"
    item = gacha_calculator.multiple_pulls(bannerName, 10)

    for i in range(len(item)):
        print(item[i])

main()