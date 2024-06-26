from numpy.random import choice
from pandas import DataFrame, concat, Timestamp
from sqlquery import DatabaseManager

class GachaCalculator(DatabaseManager):
    def __init__(self, db_name: str, userName: str):
        super().__init__(db_name)

        self.GuaranteRate = 142
        self.gachaDiamondsUsed = 142

        # Rate กาชา
        self.gachaRate = super().get_rate_item()
        self.userName = userName

        # ดึงข้อมูล user gacha detail ล่าสุดขึ้นมา
        self.thisUser = super().get_user_detail(userName)

    def getItemGacha(self, tier: str, bannerName: str):
        # ดึงข้อมูล BannerTypeID
        bannerTypeID = super().getBannerTypeID(bannerName)
        
        thisUser = self.thisUser[self.thisUser.BannerTypeID == bannerTypeID].iloc[0]
        index = (self.thisUser.loc[(self.thisUser == bannerTypeID).any(axis=1)].index[0])

        # +1 Roll
        thisUser["NumberRoll"] += 1

        # random
        # ถ้า NumberRoll ที่ GuaranteRate จะได้ SSR
        # ถ้าไม่จะ สุ่ม N ถึง SR
        if tier == "SSR" or thisUser["NumberRoll"] > self.GuaranteRate:
            item, thisUser = self.get_SSR_Item(thisUser, bannerName)
        else:
            # Get สิ่งที่สุ่มมาได้
            gachaItems = super().get_gacha_item(is_ssr=False)

            # Filter Tier
            gachaItems = gachaItems[gachaItems.TierName == tier]

            # normalize Probabilities ให้รวมกัน = 1
            gachaItems = self.normalize_Probabilities(gachaItems)
            probabilities = gachaItems["Rate_Up"].to_list()
            chosen_idx = choice(len(gachaItems), replace=True, size=1, p=probabilities)[0]
            data = gachaItems.iloc[chosen_idx].to_dict()
            ID = [*data["Name"]][0]
            # ตัวละครที่สุ่มได้ N-SR
            item = {
                "Character_ID": ID,
                "Name": data["Name"],
                "TierName": data["TierName"],
                "Salt": data["Salt"],
            }
        '''
        gacha user detail 
            จะเก็บว่า user นี้สุ่มตู้ ถาวร กับ Limited ไปแล้วเท่าไหร่ และตู้นั้นมีการันตีหรือไม่

        จะ Update NumberRoll และ การันตีว่าเป็น True หรือ False ตามตู้ที่สุ่ม
        '''

        # Update ค่าใน Value แทนการไป Getข้อมูลใหม่ที่รอบ แล้วไป Update หลังสุ่มเสร็จแทน
        self.thisUser.loc[index, "IsGuaranteed"] = thisUser["IsGuaranteed"]
        self.thisUser.loc[index, "NumberRoll"] = thisUser["NumberRoll"]
        
        data_log = {
            "User_ID": thisUser["UserID"],
            "Character_ID": item["Character_ID"],
            "Create_Date": Timestamp("now"),
            "Banner_Type_ID": bannerTypeID,
        }
        df_log = DataFrame([data_log])
        return item, df_log

    def normalize_Probabilities(self, rate_Items):
        total_probability = rate_Items["Rate_Up"].sum()
        for index, _ in rate_Items.iterrows():
            rate_Items.loc[index, "Rate_Up"] /= total_probability
        return rate_Items

    def get_SSR_Item(self, thisUser, bannerName: str):
        # Get ตัวละครที่สามารถสุ่มได้ขึ้นมา ตามตู้ที่เลือกสุ่ม
        bannerItem = super().get_gacha_item(is_ssr=True, bannerName=bannerName)

        # ดึง ประเภทของ Banner (Permanent กับ Limited)
        bannerTypes = super().list_banner_type()

        # ดึง ID ของ ประเภทของตู้ที่เลือก
        BannerTypeID = bannerItem[bannerItem.BannerName == bannerName].BannerTypeID.iloc[0]

        # มีการันตีหรือไม่
        if thisUser.IsGuaranteed == True:
            # ได้ตามตู้ที่เลือกสุ่มแน่นอน
            thisUser.IsGuaranteed = 0
        else:
            # สุ่มได้ Permanent กับ Limited
            chosen_idx = choice(len(bannerTypes), replace=True, size=1)[0]
            banner = bannerTypes[chosen_idx]
            if banner["Name"] == "Permanent":
                thisUser.IsGuaranteed = 1
            else:  # สุ่มได้ Limited
                thisUser.IsGuaranteed = 0
            # Assign ประเภทของ Banner Type ID ใหม่ที่สุ่มได้
            BannerTypeID = banner["ID"]

        # Reset NumberRoll
        thisUser.NumberRoll = 0

        # Filter ตัวละครตามประเภทตู้ที่ได้จาก if else
        bannerItem = bannerItem[bannerItem.BannerTypeID == BannerTypeID]
        bannerItem = self.normalize_Probabilities(bannerItem)
        probabilities = bannerItem["Rate_Up"].to_list()
        chosen_idx = choice(len(bannerItem), replace=True, size=1, p=probabilities)[0]
        data = bannerItem.iloc[chosen_idx].to_dict()

        # assign ค่าลง ตัวละครตามประเภทตู้ที่ได้จาก if else
        C_ID = [*data["Name"]][0]
        item = {
            "Character_ID": C_ID,
            "Name": data["Name"],
            "TierName": data["TierName"],
            "Salt": data["Salt"],
        }
        return item, thisUser

    # สุ่ม 1 โล แต่ Functionนี้ จะไม่ถูกใช้งานข้างนอก ให้ใช้ multiple_pulls(1) แทน
    def single_pull(self, bannerName: str):
        items = self.gachaRate
        item_list = list(items.keys())
        probabilities = list(items.values())
        tier = choice(item_list, size=1, replace=True, p=probabilities)[0]
        return self.getItemGacha(tier, bannerName)

    # Check Gem
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
        user_log = DataFrame(
            columns=["User_ID", "Character_ID", "Create_Date", "Banner_Type_ID"]
        )

        salt = 0

        # สุ่มกาชา
        for _ in range(num_pulls):
            item, df_new = self.single_pull(bannerName)

            # update user log
            if len(user_log) < 1:
                user_log = df_new
            else:
                user_log = concat([user_log, df_new], ignore_index=True)
            salt += item["Salt"]
            results.append(item)
        userID = self.thisUser["UserID"].iloc[0]
        
        # update gem salt
        super().update_gem(gem, salt, userID)

        # Update ครั้งเดียวหลังจาก สุ่มกาชาหมดแล้ว
        bannerTypeID = super().getBannerTypeID(bannerName)
        thisUser = self.thisUser[self.thisUser.BannerTypeID == bannerTypeID].iloc[0]
        super().update_user_detail(thisUser)

        super().insertUserGachaLog(user_log)


        return results


if __name__ == "__main__":
    # Connect to SQLite database
    pass
