import randomGacha as gacha
import sys
import os

def get_db_file():
    if getattr(sys, '_MEIPASS', None):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    # สร้าง path ไปยังไฟล์ font
    return os.path.join(base_path, "Assets", "database.db")

userName = "admin"

def main():
    gacha_calculator = gacha.GachaCalculator(get_db_file(), userName)
    printAvableBanner(gacha_calculator)
    bannerName = "Rate-Up Mild-R"
    
    item = gacha_calculator.multiple_pulls(bannerName, 10)
    userDeatail = gacha_calculator.getUserDetail(userName, bannerName).iloc[0]
    print("เพชรคงเหลือ: ", gacha_calculator.checkGem(0)[1])
    print(
        f"BannerName: {userDeatail.BannerName}\tGuaranteed: {userDeatail.IsGuaranteed}\tNumberRoll: {userDeatail.NumberRoll}\tเศษเกลือ: {userDeatail.Salt}"
    )
    for i in range(len(item)):
        print("Name: %20s,\t Tier: %3s"%(item[i]["Name"], item[i]["TierName"]))

def printAvableBanner(gacha_calculator):
    available_banners = gacha_calculator.getAvableBanner()
    for i in range(len(available_banners)):
        print("Banner Name: ", available_banners[i]["Name"])
        print("Start Date: ", available_banners[i]["start_date"])
        print("End Date: ", available_banners[i]["end_date"])
        print()
main()