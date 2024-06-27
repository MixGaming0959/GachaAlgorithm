import sqlite3

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name

    def connect(self):
        return sqlite3.connect(self.db_name)

    def execute_query(self, query, params=None):
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def execute_many(self, query, data):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data)
            conn.commit()

    def get_user_gem(self, username: str):
        query = '''
        SELECT Gem
        FROM user
        WHERE UserName = ?
        '''
        result = self.execute_query(query, (username,))
        if result:
            return result[0][0]  # คืนค่า Gem ถ้าพบข้อมูล
        else:
            return None  # คืนค่า None ถ้าไม่พบข้อมูล

    def getUserDetail(self, userName: str, bannerName: str):
        query = '''
        SELECT Banner.Name as BannerName, IsGuaranteed, NumberRoll, Salt FROM user_gacha_detail
            INNER JOIN User ON user_gacha_detail.User_ID = User.ID
            INNER JOIN Banner ON user_gacha_detail.Banner_Type_ID = Banner.Banner_Type_ID
        WHERE user.userName = ? AND Banner.Name = ?;
        '''
        result = self.execute_query(query, (userName, bannerName))
        # ยังไงก็มีแค่ 1 row อยู่ดี
        if len(result) <= 0:
            raise ValueError(f"User '{userName}' not found")
        return [dict(zip(['BannerName', 'IsGuaranteed', 'NumberRoll', 'Salt'], row)) for row in result][0]

    def insertUserGachaLog(self, user_log):
        query = '''
        INSERT INTO user_gacha_log (User_ID, Character_ID, Create_Date, Banner_Type_ID)
        VALUES (?, ?, current_timestamp, ?)
        '''

        self.execute_many(query, [(log['User_ID'], log['Character_ID'], log['Banner_Type_ID']) for log in user_log])

    def update_user_detail(self, user):
        query = '''
        UPDATE user_gacha_detail 
        SET IsGuaranteed = ?, NumberRoll = ?, Updated_Date = current_timestamp
        WHERE User_ID = ? AND Banner_Type_ID = ?;
        '''
        self.execute_query(query, (user['IsGuaranteed'], user['NumberRoll'], user['UserID'], user['BannerTypeID']))

    def getBannerTypeID(self, bannerName: str):
        query = 'SELECT banner_type_id as BannerTypeID FROM banner WHERE Name = ?'
        result = self.execute_query(query, (bannerName,))
        if result:
            return result[0][0]
        else:
            raise ValueError(f"Banner '{bannerName}' not found")

    def get_user_detail(self, userName: str):
        query = '''
        SELECT user.id as UserID, banner_type.ID as BannerTypeID, banner_type.Name as BannerType, IsGuaranteed, NumberRoll 
        FROM user_gacha_detail 
            INNER JOIN user ON user_gacha_detail.User_ID = user.id
            INNER JOIN banner_type ON user_gacha_detail.Banner_Type_ID = banner_type.id
        WHERE user.userName = ? ;
        '''
        result = self.execute_query(query, (userName,))

        if len(result) < len(self.list_banner_type()):
            self.insertUserDetail(userName, result)
            result = self.get_user_detail(userName)
        return [dict(zip(['UserID', 'BannerTypeID', 'BannerType', 'IsGuaranteed', 'NumberRoll'], row)) for row in result]

    # จะเพิ่มข้อมูลใหม่ ถ้ายังไม่มี
    def insertUserDetail(self, userName: str, result: list):
        query = '''
        INSERT INTO user_gacha_detail
            (Banner_Type_ID, User_ID, IsGuaranteed, NumberRoll, Updated_Date)
        VALUES (?, (SELECT ID FROM User Where userName = ?), 0, 0, current_timestamp)
        '''
        banner_Types = self.list_banner_type()

        already_Banner_Type_ID = [item[1] for item in result]
        newData = [(banner['ID'], userName) for banner in banner_Types if banner['ID'] not in already_Banner_Type_ID]
        self.execute_many(query, newData)

    def get_rate_item(self):
        query = 'SELECT Name, Rate FROM character_tier'
        result = self.execute_query(query)
        data = {row[0]: row[1] for row in result}
        total_probability = sum(data.values())
        return {k: round(v / total_probability, 5) for k, v in data.items()}

    def getGemFromUser(self, userName: str):
        query = 'SELECT Gem FROM user WHERE userName = ?'
        result = self.execute_query(query, (userName,))
        return result[0][0] if result else 0

    def update_gem(self, gem: int, salt: int, userID: int):
        query = '''
        UPDATE user SET Gem = ?, Salt = Salt + ?, Update_Date = current_timestamp
        WHERE ID = ?;
        '''
        self.execute_query(query, (gem, salt, userID))

    def getAvableBanner(self):
        query = 'SELECT Name, start_date, end_date FROM banner WHERE isEnable = 1'
        result = self.execute_query(query)
        return [dict(zip(['Name', 'start_date', 'end_date'], row)) for row in result]

    def get_gacha_item(self, is_ssr: bool = False, bannerName: str = 'Permanent'):
        where_clause = 'WHERE ch.Is_SSR = ?'
        params = [1 if is_ssr else 0]
        if is_ssr:
            where_clause += ' AND bru.Banner_ID in ( SELECT ID FROM banner WHERE Name in (?, ?))'
            params.extend(['Permanent', bannerName])

        query = f'''
        SELECT ch.ID as Character_ID, ch.Name, tier.Name as TierName, 
            Banner.Name as BannerName, bt.ID as BannerTypeID, 
            bt.Name as BannerTypeName, tier.Salt, bru.Rate_Up as Rate_Up
        FROM `character` as ch
            INNER JOIN character_tier tier ON ch.Tier_ID = tier.id
            INNER JOIN banner_rate_up bru on bru.charcter_id = ch.id
            INNER JOIN Banner on Banner.ID = bru.Banner_ID
            INNER JOIN banner_type bt on bt.ID = Banner.banner_type_id 
        {where_clause}
        '''
        result = self.execute_query(query, params)
        output = [dict(zip(['Character_ID', 'Name', 'TierName', 'BannerName', 'BannerTypeID', 'BannerTypeName', 'Salt', 'Rate_Up'], row)) for row in result]
        if len(output) <= 0:
            raise Exception(f"No Banner ({bannerName}) in database")
        return output
    
    def list_banner_type(self):
        query = 'SELECT * FROM banner_type'
        result = self.execute_query(query)
        return [dict(zip(['ID', 'Name'], row)) for row in result]

if __name__ == "__main__":
    # Connect to SQLite database
    db_name = "database.db"
    db_manager = DatabaseManager(db_name)
    userName = "admin"

    # Get rate items
    item = db_manager.getGemFromUser(userName)