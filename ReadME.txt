pip install -r requirements.txt
ใช้เพื่อให้ version library ตรงกัน
---------------------------------------------
v 1.0
สร้าง อัลกอริทึมสุ่ม gacha
---------------------------------------------
v 2.0
เปลี่ยนฐานข้อมูลไปเก็บใน database.db
---------------------------------------------
V 3.0
เพิ่ม เพชรที่ใช้ในการสุ่ม
-- FIX
แก้ไข Character ID ที่ได้จากการสุ่มไม่ใช่ Character_ID จริงๆ แต่เป็น index
-- TODO
ยังไม่มีระบบแลกเกลือเป็นเพชร
---------------------------------------------
V 3.1
ลบ env กับใส่ version ลง requirements
---------------------------------------------
V 3.2
ลดภาระในการUpdate User และแก้ getNextID_UserLog แต่ไม่มีข้อมูลในGet และ update_user_detail ใส่ WHERE ผิดที่
---------------------------------------------
V 4.0
เพิ่ม ตู้ RateUp 
เช่น Rate-Up Debirun
Name, Rate
Beta AMI, 1
Xonebu X’thulhu, 1
Mild-R, 1
Kumoku Tsururu, 1
Debirun, 2
T-Reina Ashyra, 2
ตอนนี้มี RateUp แค่ World-End
ตู้อื่นRateเท่าเดิม
---------------------------------------------
V 5.0
เปลี่ยน Library
เอา pandas และ numpy ออก
ใช้ sqlite3 แทน
---------------------------------------------
V 5.1
Refactor Code
---------------------------------------------
V 5.2
# insertUserGachaDetail
# insert ก็ต่อเมื่อ user คนนั้นสุ่มตู้ประเภทนั้นครั้งแรก
fix insertUserGachaDetail
ก่อนหน้านี้มันจะInsert BannerType ทุกอัน ถึงแม้ว่าจะมีหรือแล้วก็ตาม
---------------------------------------------