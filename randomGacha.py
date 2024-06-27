import os
import sys
from random import choices
from datetime import datetime
from sqlquery import DatabaseManager

def get_db_file():
    if getattr(sys, '_MEIPASS', None):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    # สร้าง path ไปยังไฟล์ db
    return os.path.join(base_path, "Assets", "database.db")

class GachaCalculator(DatabaseManager):
    def __init__(self, userName: str):
        db_name = get_db_file()
        super().__init__(db_name)

        # จำนวนครั้งในการการันตี
        self.GuaranteRate = 142
        # จำนวน gem ที่ใช้ต่อการสุ่ม 1 ครั้ง
        self.gachaDiamondsUsed = 1

        # Rate กาชา
        self.gachaRate = super().get_rate_item()
        self.userName = userName

        # ดึงข้อมูล user gacha detail ล่าสุดขึ้นมา
        self.thisUser = super().get_user_detail(userName)

    def getItemGacha(self, tier: str, bannerName: str):
        # ดึงข้อมูล BannerTypeID
        bannerTypeID = super().getBannerTypeID(bannerName)
        
        thisUser = next(user for user in self.thisUser if user["BannerTypeID"] == bannerTypeID)
        index = next(i for i, user in enumerate(self.thisUser) if user["BannerTypeID"] == bannerTypeID)

        # +1 Roll
        thisUser["NumberRoll"] += 1

        if tier == "SSR" or thisUser["NumberRoll"] > self.GuaranteRate:
            gachaItems, thisUser = self.get_SSR_Item(thisUser, bannerName)
            tier = "SSR"
        else:
            # Get สิ่งที่สุ่มมาได้
            gachaItems = super().get_gacha_item(is_ssr=False)

        # Filter Tier
        gachaItems = [item for item in gachaItems if item["TierName"] == tier]

        # normalize Probabilities
        gachaItems = self.normalize_Probabilities(gachaItems)
        probabilities = [item["Rate_Up"] for item in gachaItems]
        chosen_idx = choices(range(len(gachaItems)), weights=probabilities, k=1)[0]
        data = gachaItems[chosen_idx]

        # ตัวละครที่สุ่มได้ N-SR
        item = {
            "Character_ID": data["Character_ID"],
            "Name": data["Name"],
            "TierName": data["TierName"],
            "Salt": data["Salt"],
        }

        # Update ค่าใน Value
        self.thisUser[index]["IsGuaranteed"] = thisUser["IsGuaranteed"]
        self.thisUser[index]["NumberRoll"] = thisUser["NumberRoll"]
        
        data_log = {
            "User_ID": thisUser["UserID"],
            "Character_ID": item["Character_ID"],
            "Create_Date": datetime.now().isoformat(),
            "Banner_Type_ID": bannerTypeID,
        }
        return item, [data_log]

    def normalize_Probabilities(self, rate_Items):
        total_probability = sum(item["Rate_Up"] for item in rate_Items)
        for item in rate_Items:
            item["Rate_Up"] /= total_probability
        return rate_Items

    def get_SSR_Item(self, thisUser, bannerName: str):
        # Get ตัวละครที่สามารถสุ่มได้ขึ้นมา ตามตู้ที่เลือกสุ่ม
        bannerItem = super().get_gacha_item(is_ssr=True, bannerName=bannerName)

        # ดึง ประเภทของ Banner (Permanent กับ Limited)
        bannerTypes = super().list_banner_type()

        # ดึง ID ของ ประเภทของตู้ที่เลือก
        BannerTypeID = next(item["BannerTypeID"] for item in bannerItem if item["BannerName"] == bannerName)

        # มีการันตีหรือไม่
        if thisUser["IsGuaranteed"] == True:
            # ได้ตามตู้ที่เลือกสุ่มแน่นอน
            thisUser["IsGuaranteed"] = 0
        else:
            # สุ่มประเภทของ Banner ได้ Permanent กับ Limited
            chosen_idx = choices(range(len(bannerTypes)), k=1)[0]
            banner = bannerTypes[chosen_idx]
            if banner["Name"] == "Permanent":
                thisUser["IsGuaranteed"] = 1
            else:  # สุ่มได้ Limited
                thisUser["IsGuaranteed"] = 0
            # Assign ประเภทของ Banner Type ID ใหม่ที่สุ่มได้
            BannerTypeID = banner["ID"]

        # Reset NumberRoll
        thisUser["NumberRoll"] = 0

        # Filter ตัวละครตามประเภทตู้ที่ได้จาก if else
        bannerItem = [item for item in bannerItem if item["BannerTypeID"] == BannerTypeID]

        return bannerItem, thisUser

    def single_pull(self, bannerName: str):
        items = self.gachaRate
        item_list = list(items.keys())
        probabilities = list(items.values())
        tier = choices(item_list, weights=probabilities, k=1)[0]
        return self.getItemGacha(tier, bannerName)

    def checkGem(self, num_pulls:int):
        gem = super().getGemFromUser(self.userName)
        if gem < num_pulls*self.gachaDiamondsUsed:
            return False, 0
        remaining_diamonds = int(gem-(num_pulls*self.gachaDiamondsUsed))
        return True, remaining_diamonds
    
    def multiple_pulls(self, bannerName: str, num_pulls: int):
        # ดึงข้อมูล User จาก Database อีกรอบ
        self.thisUser = super().get_user_detail(self.userName)

        # Check ว่า Gem พอหรือไม่
        condition, gem = self.checkGem(num_pulls)
        if not condition:
            return {"Error": "Not Enough Gem"}

        results = []
        user_log = []

        salt = 0

        # สุ่มกาชา
        for _ in range(num_pulls):
            item, df_new = self.single_pull(bannerName)

            # update user log
            user_log.extend(df_new)
            salt += item["Salt"]
            results.append(item)
        userID = self.thisUser[0]["UserID"]
        
        # update gem salt
        super().update_gem(gem, salt, userID)

        # Update ครั้งเดียวหลังจาก สุ่มกาชาหมดแล้ว
        bannerTypeID = super().getBannerTypeID(bannerName)
        thisUser = next(user for user in self.thisUser if user["BannerTypeID"] == bannerTypeID)
        super().update_user_detail(thisUser)

        super().insertUserGachaLog(user_log)

        return results

if __name__ == "__main__":
    # Connect to SQLite database
    pass