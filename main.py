import flet as ft
from supabase import create_client, Client
import re
import tkinter as tk
from tkinter import filedialog

# =========================================================================
# --- SUPABASE DATABASE CONNECTION ---
# =========================================================================
SUPABASE_URL = "https://ryberrmhwmjnqcovpxrv.supabase.co"
SUPABASE_KEY = "sb_publishable_7JG5cYQrpnme8TnImrqLCQ_z9RZSvPi"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_notification(title, message):
    try:
        supabase.table("notifications").insert({"title": title, "message": message}).execute()
    except Exception as ex:
        print(f"Notification Error: {ex}")
# မိမိ App ရဲ့ လက်ရှိ Version သတ်မှတ်ချက်
CURRENT_VERSION = "1.0.0"

def check_app_version(page: ft.Page):
    try:
        res = supabase.table("app_settings").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            server_version = res.data[0].get("latest_version")
            download_url = res.data[0].get("update_url")

            # လက်ရှိ Version ထက် Cloud က Version က ပိုသစ်နေပါက
            if server_version and server_version != CURRENT_VERSION:
                
                update_dialog = ft.AlertDialog(
                    modal=True, # အပြင်ဘက်နှိပ်ပြီး ပိတ်လို့မရအောင် ထိန်းထားခြင်း
                    title=ft.Text("⚠️ App Update ရရှိနိုင်ပါပြီ", weight="bold", color="red"),
                    content=ft.Text(f"အက်ပ် Version အသစ် (v{server_version}) ထွက်ရှိနေပါသည်။\nပုံမှန် အသုံးပြုနိုင်ရန် Update ပြုလုပ်ပေးပါ။"),
                    actions=[
                        ft.ElevatedButton(
                            "Update ပြုလုပ်မည်", 
                            icon=ft.Icons.DOWNLOAD,
                            bgcolor="green", 
                            color="white",
                            on_click=lambda _: page.launch_url(download_url) # Download Link သို့ ပို့ပေးမည်
                        )
                    ]
                )
                page.overlay.append(update_dialog)
                update_dialog.open = True
                page.update()
    except Exception as ex:
        print(f"Version Check Error: {ex}")
# Version Update Download        

        
def main(page: ft.Page):
    page.title = "Teacher Match"
    check_app_version(page)
    page.theme_mode = "light"

    def open_update_dialog(e):
        try:
            res = supabase.table("app_settings").select("*").eq("id", 1).execute()
            
            if res.data and len(res.data) > 0:
                server_version = res.data[0].get("latest_version")
                download_url = res.data[0].get("update_url")
            else:
                server_version = CURRENT_VERSION
                download_url = "https://your-apk-link.com"

            if server_version == CURRENT_VERSION:
                status_text = f"သင့် App သည် နောက်ဆုံးပေါ် Version (v{CURRENT_VERSION}) ဖြစ်နေပါပြီ။"
                btn_text = "ကျေးဇူးတင်ပါသည်"
                btn_color = "grey"
            else:
                status_text = f"Version အသစ် (v{server_version}) ထွက်ရှိနေပါသည်။\n(လက်ရှိ - v{CURRENT_VERSION})"
                btn_text = "Download/Update ပြုလုပ်မည်"
                btn_color = "green"

            dlg = ft.AlertDialog(
                title=ft.Text("📱 App Version & Update", weight="bold"),
                content=ft.Column([
                    ft.Text(status_text, size=13),
                ], tight=True),
                actions=[
                    ft.ElevatedButton(
                        btn_text, 
                        icon=ft.Icons.DOWNLOAD,
                        bgcolor=btn_color, 
                        color="white",
                        on_click=lambda _: [page.launch_url(download_url) if (server_version != CURRENT_VERSION and download_url) else None, setattr(dlg, 'open', False), page.update()]
                    ),
                    ft.TextButton("ပိတ်မည်", on_click=lambda _: [setattr(dlg, 'open', False), page.update()])
                ]
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        except Exception as ex:
            print(f"Update Tab Error: {ex}")
    
    page.window_width = 420
    page.window_height = 780
    page.window_resizable = False  
    page.window_maximized = False  
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    
    # Session Variables
    page.is_admin_logged_in = False 
    page.logged_in_tutor_id = None 
    page.admin_selected_chat_tutor_id = None  
    
    # Student Session Variables
    page.logged_in_student_id = None
    page.logged_in_student_name = ""
    page.logged_in_student_phone = ""
    # =========================================================================
    # --- APP BAR (BACK NAVIGATION) ---
    # =========================================================================
    def update_appbar(is_home, title=""):
        if is_home:
            page.appbar = None
        else:
            page.appbar = ft.AppBar(
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: go_to_home()),
                title=ft.Text(title, size=16, weight="bold"),
                center_title=True,
                bgcolor="#E0E0E0"
            )
        page.update()

    def go_to_home():
        main_container.content = home_view
        update_appbar(True)

    def navigate_to(view_content, title):
        main_container.content = view_content
        update_appbar(False, title)
        if title == "Admin Panel" and page.is_admin_logged_in: refresh_admin_view()
        if title == "Student Area" and page.logged_in_student_id: refresh_student_view()
        if title == "Black Listed": refresh_blacklist_view()

    # =========================================================================
    # --- တိုင်း/ပြည်နယ် စာရင်း ---
    # =========================================================================
    location_data_states = [
        "ရန်ကုန်တိုင်းဒေသကြီး", 
        "မန္တလေးတိုင်းဒေသကြီး", 
        "ပဲခူးတိုင်းဒေသကြီး", 
        "နေပြည်တော်"
    ]
    
    grade_options = [
        ft.dropdown.Option("မူလတန်း / Primary"), 
        ft.dropdown.Option("အလယ်တန်း / Middle"), 
        ft.dropdown.Option("အထက်တန်း/ Hight"), 
        ft.dropdown.Option("IGCSE"), 
        ft.dropdown.Option("GED"),
        ft.dropdown.Option("အခြား")
    ]

    def select_and_send_image(sender_type):
        root = tk.Tk()
        root.attributes('-topmost', True) 
        root.withdraw() 
        
        file_path = filedialog.askopenfilename(
            title="ဓာတ်ပုံရွေးချယ်ပါ", 
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        root.destroy()
        
        if file_path:
            if sender_type == "teacher" and page.logged_in_tutor_id:
                supabase.table("chat_messages").insert({
                    "tutor_id": page.logged_in_tutor_id,
                    "sender": "teacher",
                    "message": "[ဓာတ်ပုံ]",
                    "image_data": file_path
                }).execute()
                refresh_teacher_chat_view()
                if page.is_admin_logged_in: refresh_admin_chat_view()
                
            elif sender_type == "admin" and page.admin_selected_chat_tutor_id:
                supabase.table("chat_messages").insert({
                    "tutor_id": page.admin_selected_chat_tutor_id,
                    "sender": "admin",
                    "message": "[ဓာတ်ပုံ]",
                    "image_data": file_path
                }).execute()
                open_chat_with_teacher(page.admin_selected_chat_tutor_id)
                refresh_teacher_chat_view()

    # =========================================================================
    # --- ၁။ TEACHER TAB ---
    # =========================================================================
    login_username = ft.TextField(label="Username", border_color="#d1d9e6", bgcolor="white")
    login_password = ft.TextField(label="Password", password=True, border_color="#d1d9e6", bgcolor="white")
    login_msg = ft.Text(color="red")
    
    reg_username = ft.TextField(label="Username (ဥပမာ - KyawKyaw)")
    reg_password = ft.TextField(label="Password အသစ် (ဥပမာ - Kk@12345)", password=True)
    reg_msg = ft.Text(color="red")
    
    # Profile ဓာတ်ပုံ ဖော်ပြရန် UI Component များ
    profile_img_preview = ft.Image(src="", width=120, height=120, fit="cover", border_radius=60, visible=False)
    photo_input = ft.TextField(label="ဓာတ်ပုံ လမ်းကြောင်း", disabled=True, expand=True)
    select_photo_btn = ft.ElevatedButton("📷 ဓာတ်ပုံ ရွေးပါ", disabled=True)

    def pick_profile_photo(e):
        root = tk.Tk()
        root.attributes('-topmost', True)
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Profile ဓာတ်ပုံရွေးပါ",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        root.destroy()
        if file_path:
            photo_input.value = file_path
            profile_img_preview.src = file_path
            profile_img_preview.visible = True
            page.update()

    select_photo_btn.on_click = pick_profile_photo
    
    name_input = ft.TextField(label="ဆရာ/ဆရာမ အမည်", disabled=True)
    gender_input = ft.Dropdown(label="ကျား / မ", options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female")], disabled=True)
    phone_input = ft.TextField(label="ဆက်သွယ်ရန် ဖုန်းနံပါတ်", keyboard_type=ft.KeyboardType.PHONE, disabled=True)
    bio_input = ft.TextField(label="ကိုယ်ရေးအကျဉ်း (Bio)", multiline=True, min_lines=2, max_lines=3, disabled=True)
    
    state_input = ft.Dropdown(label="တိုင်း/ပြည်နယ်", options=[ft.dropdown.Option(s) for s in location_data_states], disabled=True)
    township_input = ft.TextField(label="မြို့နယ် (စာဖြင့်ရိုက်ပါ)", disabled=True)
    
    curriculum_input = ft.Dropdown(label="သင်ရိုးစနစ် (Curriculum)", options=[ft.dropdown.Option("Government"), ft.dropdown.Option("International"), ft.dropdown.Option("Dual")], disabled=True)
    teaching_mode_input = ft.Dropdown(
        label="သင်ကြားမည့်စနစ်",  
        options=[ft.dropdown.Option("Online"), ft.dropdown.Option("Inperson"), ft.dropdown.Option("Online & Inperson")], 
        disabled=True
    )
    
    grade_input1 = ft.Dropdown(label="သင်ကြားမည့် အတန်း (၁)", options=grade_options, disabled=True)
    subject_input1 = ft.TextField(label="ဘာသာရပ် (၁)", disabled=True)
    grade_input2 = ft.Dropdown(label="သင်ကြားမည့် အတန်း (၂)", options=grade_options, disabled=True)
    subject_input2 = ft.TextField(label="ဘာသာရပ် (၂)", disabled=True)
    grade_input3 = ft.Dropdown(label="သင်ကြားမည့် အတန်း (၃)", options=grade_options, disabled=True)
    subject_input3 = ft.TextField(label="ဘာသာရပ် (၃)", disabled=True)
    grade_input4 = ft.Dropdown(label="သင်ကြားမည့် အတန်း (၄)", options=grade_options, disabled=True)
    subject_input4 = ft.TextField(label="ဘာသာရပ် (၄)", disabled=True)
    
    days_input = ft.Dropdown(label="သင်ကြားနိုင်မည့် ရက်များ", options=[ft.dropdown.Option("ရုံးဖွင့်ရက်"), ft.dropdown.Option("ရုံးပိတ်ရက်"), ft.dropdown.Option("နေ့တိုင်း")], disabled=True)
    time_input = ft.Dropdown(label="တစ်ရက် သင်ကြားနိုင့်မည့် အချိန်", options=[ft.dropdown.Option("မနက်"), ft.dropdown.Option("နေ့လည်"), ft.dropdown.Option("ညနေ"),ft.dropdown.Option("တစ်ရက်လုံး"),ft.dropdown.Option("မနက် နှင့် ညနေ"),ft.dropdown.Option("နေ့လည် နှင့် ညနေ"),ft.dropdown.Option("မနက် နှင့် နေ့လည်")], disabled=True)
    current_time_remark_input = ft.TextField(label="မှတ်ချက် (လက်ရှိသင်ကြားနိုင်သောအချိန်)", disabled=True)
    fee_input = ft.TextField(label="လစဉ်ကြေး (ကျပ်)", disabled=True)
    register_msg = ft.Text(color="green")

    teacher_chat_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    teacher_chat_input = ft.TextField(label="Admin ဆီ စာပို့ရန်...", expand=True)
    teacher_completed_students_list = ft.ListView(spacing=5, expand=False, height=120)

    def send_teacher_message(e):
        if not teacher_chat_input.value or page.logged_in_tutor_id is None: return
        supabase.table("chat_messages").insert({
            "tutor_id": page.logged_in_tutor_id,
            "sender": "teacher",
            "message": teacher_chat_input.value,
            "image_data": None
        }).execute()
        teacher_chat_input.value = ""
        refresh_teacher_chat_view()
        if page.is_admin_logged_in: refresh_admin_chat_view()

    def refresh_teacher_chat_view():
        teacher_chat_list.controls.clear()
        if page.logged_in_tutor_id is None: return
        
        res = supabase.table("chat_messages").select("*").eq("tutor_id", page.logged_in_tutor_id).order("timestamp").execute()
        for row in res.data:
            sender = row.get("sender")
            msg = row.get("message")
            img_data = row.get("image_data")
            
            align = ft.MainAxisAlignment.END if sender == "teacher" else ft.MainAxisAlignment.START
            color = "#DCEFFA" if sender == "teacher" else "#EAEAEA"
            prefix = "Me: " if sender == "teacher" else "Admin: "
            
            if img_data:
                content_ui = ft.Column([
                    ft.Text(f"{prefix} ပုံပို့ထားပါသည်", size=10, color="grey"),
                    ft.Image(src=img_data, width=150, height=150, fit="cover", border_radius=5)
                ])
            else:
                content_ui = ft.Text(f"{prefix}{msg}", size=13)
                
            teacher_chat_list.controls.append(ft.Row([ft.Container(content=content_ui, bgcolor=color, padding=8, border_radius=10)], alignment=align))
        page.update()

    teacher_chat_container = ft.Column([
        ft.Text("Admin နှင့် စကားပြောရန် Panel", weight="bold", size=14, color="blue"), ft.Divider(),
        teacher_chat_list,
        ft.Row([
            teacher_chat_input, 
            ft.IconButton(ft.Icons.IMAGE, icon_color="blue", on_click=lambda _: select_and_send_image("teacher")),
            ft.IconButton(ft.Icons.SEND, on_click=send_teacher_message)
        ])
    ], expand=True)

    def set_form_disabled(status: bool):
        name_input.disabled = status; gender_input.disabled = status; phone_input.disabled = status
        bio_input.disabled = status; state_input.disabled = status; township_input.disabled = status; curriculum_input.disabled = status; teaching_mode_input.disabled = status
        grade_input1.disabled = status; subject_input1.disabled = status
        grade_input2.disabled = status; subject_input2.disabled = status
        grade_input3.disabled = status; subject_input3.disabled = status
        grade_input4.disabled = status; subject_input4.disabled = status
        days_input.disabled = status; time_input.disabled = status; current_time_remark_input.disabled = status
        fee_input.disabled = status; select_photo_btn.disabled = status

    def switch_to_edit_mode(e):
        set_form_disabled(False)
        view_mode_buttons.visible = False; edit_mode_buttons.visible = True; page.update()

    def cancel_edit_mode(e):
        set_form_disabled(True)
        view_mode_buttons.visible = True; edit_mode_buttons.visible = False; load_tutor_profile()

    def load_tutor_profile():
        if page.logged_in_tutor_id is None: return
        res = supabase.table("tutors").select("*").eq("id", page.logged_in_tutor_id).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            name_input.value = row.get("name")
            gender_input.value = row.get("gender")
            phone_input.value = row.get("phone")
            bio_input.value = row.get("bio")
            state_input.value = row.get("state")
            township_input.value = row.get("township")
            curriculum_input.value = row.get("curriculum")
            teaching_mode_input.value = row.get("teaching_mode")
            grade_input1.value = row.get("grade1"); subject_input1.value = row.get("subject1")
            grade_input2.value = row.get("grade2"); subject_input2.value = row.get("subject2")
            grade_input3.value = row.get("grade3"); subject_input3.value = row.get("subject3")
            grade_input4.value = row.get("grade4"); subject_input4.value = row.get("subject4")
            days_input.value = row.get("days"); time_input.value = row.get("time"); current_time_remark_input.value = row.get("current_time_remark")
            fee_input.value = row.get("fee"); photo_input.value = row.get("photo")
            
            p_photo = row.get("photo")
            if p_photo:
                profile_img_preview.src = p_photo
                profile_img_preview.visible = True
            else:
                profile_img_preview.visible = False
            
            p_stat = row.get("status")
            if p_stat == "rejected":
                register_msg.value = f"သင့် Profile ကို Admin က Reject လုပ်ထားပါသည်။ (အကြောင်းရင်း: {row.get('reject_reason')})"; register_msg.color = "red"
            elif p_stat == "blacklisted":
                register_msg.value = "သင့်အကောင့်ကို Black List သွင်းထားပါသည်။"; register_msg.color = "red"
            elif p_stat == "pending":
                if not row.get("name"):
                    register_msg.value = "အကောင့်သစ်ဖြစ်ပါသည်။ ကျေးဇူးပြု၍ 'ပြင်ဆင်မည်' ကိုနှိပ်ပြီး အချက်အလက်များ ဖြည့်သွင်းပါ။"
                    register_msg.color = "blue"
                else:
                    register_msg.value = "သင့် Profile သည် အတည်ပြုချက် စောင့်ဆိုင်းနေဆဲ ဖြစ်သည်။"; register_msg.color = "orange"
            else:
                register_msg.value = "သင့် Profile အား အတည်ပြုပြီး ဖြစ်သည်။"; register_msg.color = "green"
                
        teacher_completed_students_list.controls.clear()
        req_res = supabase.table("requests").select("student_name, student_phone").eq("tutor_id", page.logged_in_tutor_id).eq("status", "completed").execute()
        for r in req_res.data:
            teacher_completed_students_list.controls.append(ft.Text(f"• ကျောင်းသား: {r.get('student_name')} (ဖုန်း: {r.get('student_phone')})", size=12, color="green", weight="bold"))
        if not teacher_completed_students_list.controls:
            teacher_completed_students_list.controls.append(ft.Text("ချိတ်ဆက်ပြီးမြောက်သော ကျောင်းသားစာရင်း မရှိသေးပါ။", size=11, color="grey"))
        page.update()

    def save_or_update_profile(e):
        if not name_input.value or not phone_input.value or not curriculum_input.value or not grade_input1.value or not subject_input1.value or not state_input.value or not township_input.value:
            register_msg.value = "အမည်၊ ဖုန်း၊ ဒေသ၊ မြို့နယ်၊ သင်ရိုးနှင့် အနည်းဆုံး အတန်း(၁)/ဘာသာရပ်(၁) ဖြည့်ပါ။"; register_msg.color = "red"; page.update(); return
        
        supabase.table("tutors").update({
            "name": name_input.value, "gender": gender_input.value, "phone": phone_input.value, "bio": bio_input.value,
            "state": state_input.value, "township": township_input.value, "curriculum": curriculum_input.value,
            "teaching_mode": teaching_mode_input.value,
            "grade1": grade_input1.value, "subject1": subject_input1.value,
            "grade2": grade_input2.value, "subject2": subject_input2.value,
            "grade3": grade_input3.value, "subject3": subject_input3.value,
            "grade4": grade_input4.value, "subject4": subject_input4.value,
            "days": days_input.value, "time": time_input.value, "current_time_remark": current_time_remark_input.value,
            "fee": fee_input.value, "photo": photo_input.value, "status": "pending"
        }).eq("id", page.logged_in_tutor_id).execute()
        
        add_notification("Teacher Profile ပြင်ဆင်မှု", f"ဆရာ {name_input.value} က ကိုယ်ရေးအချက်အလက်သစ်များ ဖြည့်စွက်/ပြင်ဆင်လိုက်ပါသည်။")
        
        set_form_disabled(True); view_mode_buttons.visible = True; edit_mode_buttons.visible = False
        register_msg.value = "Profile သိမ်းဆည်းပြီးပါပြီ။ Admin အတည်ပြုချက် ထပ်မံစောင့်ပါ။"; register_msg.color = "green"
        if page.is_admin_logged_in: refresh_admin_view()
        page.update()

    view_mode_buttons = ft.Row([
        ft.ElevatedButton("Profile ပြင်ဆင်မည်", icon=ft.Icons.EDIT, on_click=switch_to_edit_mode, bgcolor="orange", color="white")
    ], visible=True)

    edit_mode_buttons = ft.Row([
        ft.ElevatedButton("ပြင်ဆင်ချက်များ သိမ်းဆည်းမည်", icon=ft.Icons.SAVE, on_click=save_or_update_profile, bgcolor="green", color="white"),
        ft.TextButton("မပြင်တော့ပါ (Cancel)", on_click=cancel_edit_mode)
    ], visible=False)

    def login_tutor(e):
        res = supabase.table("tutors").select("id, status").eq("username", login_username.value).eq("password", login_password.value).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            if row.get("status") == 'blacklisted':
                login_msg.value = "သင့်အကောင့်အား Blacklist သွင်းထားသဖြင့် ဝင်ရောက်ခွင့်မပြုတော့ပါ။"
                page.update()
                return
                
            page.logged_in_tutor_id = row.get("id")
            teacher_content_area.content = teacher_profile_view
            set_form_disabled(True); view_mode_buttons.visible = True; edit_mode_buttons.visible = False
            
            # --- [ဒီစာကြောင်း (၂) ကြောင်းကို အသစ်ထည့်ပါ] ---
            teacher_nav_row.visible = True
            teacher_nav_divider.visible = True
            
            load_tutor_profile()
            login_username.value = ""; login_password.value = ""; login_msg.value = ""
        else: 
            login_msg.value = "Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။"
        page.update()

    def execute_register_account(e):
        u = reg_username.value.strip()
        p = reg_password.value.strip()
        
        if not re.match(r"^([A-Z][a-z]+)+$", u):
            reg_msg.value = "Username သည် Space မပါဘဲ နာမည်အစစာလုံးတိုင်း UpperCase ဖြစ်ရပါမည် (ဥပမာ - KyawKyaw)။"
            reg_msg.color = "red"
            page.update()
            return
            
        if (len(p) < 8 or not re.search(r"[A-Z]", p) or not re.search(r"[a-z]", p) or not re.search(r"[0-9]", p) or not re.search(r"[@#$!%*?&_]", p)):
            reg_msg.value = "Password သည် အနည်းဆုံး ၈ လုံး ရှိရမည်ဖြစ်ပြီး စာလုံးကြီး၊ စာလုံးအသေး၊ ဂဏန်းနှင့် သင်္ကေတ ပါဝင်ရပါမည် (ဥပမာ - Kk@12345)။"
            reg_msg.color = "red"
            page.update()
            return
            
        try:
            supabase.table("tutors").insert({"username": u, "password": p, "status": "pending", "reject_reason": ""}).execute()
            add_notification("အကောင့်သစ်မှတ်ပုံတင်ခြင်း", f"အသုံးပြုသူ {u} က ဆရာအကောင့်အသစ်တစ်ခု လာရောက်ဆောက်လုပ်သွားပါသည်။")
            reg_msg.value = "အကောင့်ဆောက်အောင်မြင်ပါသည်။ Login စာမျက်နှာသို့ သွားပြီး ဝင်ရောက်နိုင်ပါပြီ။"
            reg_msg.color = "green"
            reg_username.value = ""; reg_password.value = ""
        except Exception:
            reg_msg.value = "ဤ Username က ရှိပြီးသား ဖြစ်နေသဖြင့် အခြားပေးပါ။"
            reg_msg.color = "red"
        page.update()

    def apply_for_job(job_id, job_subject):
        if page.logged_in_tutor_id is None:
            page.snack_bar = ft.SnackBar(ft.Text("အလုပ်လျှောက်ထားရန် ဦးစွာ Login ဝင်ပေးပါခင်ဗျာ။"))
            page.snack_bar.open = True; page.update(); return
            
        res = supabase.table("job_applications").select("id").eq("job_id", job_id).eq("tutor_id", page.logged_in_tutor_id).execute()
        if res.data and len(res.data) > 0:
            page.snack_bar = ft.SnackBar(ft.Text("ဤ Post ကို သင် လျှောက်ထားပြီး ဖြစ်ပါသည်ဗျာ။"))
            page.snack_bar.open = True; page.update(); return
            
        supabase.table("job_applications").insert({"job_id": job_id, "tutor_id": page.logged_in_tutor_id}).execute()
        
        t_res = supabase.table("tutors").select("name, username").eq("id", page.logged_in_tutor_id).execute()
        t_display = t_res.data[0].get("name") if (t_res.data and t_res.data[0].get("name")) else t_res.data[0].get("username")
        
        add_notification("ဆရာမ အလုပ်လျှောက်လွှာတင်ခြင်း", f"ဆရာ/မ [{t_display}] မှ ကျောင်းသားပို့စ် ဘာသာရပ် [{job_subject}] ကို လာရောက်လျှောက်ထားလိုက်ပါသည်။")
        page.snack_bar = ft.SnackBar(ft.Text("အလုပ်လျှောက်လွှာ အောင်မြင်စွာ တင်ပြီးပါပြီ။ Admin မှ ဆက်သွယ်ပေးပါမည်ဗျာ။"))
        page.snack_bar.open = True
        refresh_teacher_job_view()

    teacher_job_list = ft.ListView(expand=True, spacing=10)
    
    def refresh_teacher_job_view():
        teacher_job_list.controls.clear()
        res = supabase.table("job_posts").select("*").eq("status", "approved").execute()
        for row in res.data:
            j_id = row.get("id")
            subj = row.get("subject")
            j_state = row.get("state")
            town = row.get("township")
            fee = row.get("fee_offer")
            details = row.get("details")
            
            is_applied = False
            if page.logged_in_tutor_id is not None:
                app_res = supabase.table("job_applications").select("id").eq("job_id", j_id).eq("tutor_id", page.logged_in_tutor_id).execute()
                if app_res.data and len(app_res.data) > 0:
                    is_applied = True
            
            if is_applied:
                apply_button = ft.ElevatedButton("လျှောက်ထားပြီးပြီ", icon=ft.Icons.DONE, bgcolor="green", color="white", disabled=True)
            else:
                apply_button = ft.ElevatedButton("လျှောက်ထားရန် (Apply)", icon=ft.Icons.CHECK_CIRCLE, bgcolor="blue", color="white",
                                                on_click=lambda e, jid=j_id, sb=subj: apply_for_job(jid, sb))

            teacher_job_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Text(f"လိုအပ်သော ဘာသာရပ်: {subj}", weight="bold", size=16, color="blue"),
                ft.Text(f"ဒေသ: {j_state}, {town}", color="red"),
                ft.Text(f"ပေးနိုင်သောနှုန်းထား: {fee} Ks"),
                ft.Text(f"အသေးစိတ်: {details}"),
                apply_button  
            ]))))
        if not teacher_job_list.controls: teacher_job_list.controls.append(ft.Text("ကျောင်းသားများ၏ ဖိတ်ခေါ်စာ မရှိသေးပါ။", color="grey"))
        page.update()

    teacher_auth_view = ft.Column([
        ft.Text("TEACHER", size=24, weight="bold", color="#1a1a4b"),
        
        # --- Login Card ---
        ft.Container(
            content=ft.Column([
                ft.Text("Teacher Login", size=16, weight="bold", color="#2196F3"),
                login_username, 
                login_password, 
                login_msg,
                ft.Row([
                    ft.ElevatedButton(
                        "Login ဝင်မည်", on_click=login_tutor, width=150, 
                        bgcolor="#F4F6F9", color="#1a1a4b", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER), # Center ဖြစ်အောင်လုပ်ခြင်း
            bgcolor="#F9FAFE", padding=20, border_radius=10, 
            width=350, # အကွက်ကို fixed width ပေးထားခြင်း
        ),
        
        ft.Container(height=10),
        
        # --- Register Card ---
        ft.Container(
            content=ft.Row([
                ft.Text("အကောင့်မရှိသေးပါက -", size=12, color="grey"), 
                ft.TextButton("Register အကောင့်သစ်ဆောက်ရန်", on_click=lambda _: [setattr(teacher_content_area, 'content', teacher_register_view), page.update()])
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#F9FAFE", padding=10, border_radius=10,
            width=350,
        )
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    teacher_register_view = ft.Column([
        ft.Text("Teacher Register", size=18, weight="bold", color="green"), reg_username, reg_password, reg_msg,
        ft.Button("အကောင့်သစ် မှတ်ပုံတင်မည်", on_click=execute_register_account, width=220), ft.Divider(),
        ft.TextButton("Login စာမျက်နှာသို့ ပြန်သွားမည်", on_click=lambda _: [setattr(teacher_content_area, 'content', teacher_auth_view), setattr(reg_msg, 'value', ""), page.update()])
    ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

    teacher_profile_view = ft.Column([
        ft.Row([profile_img_preview], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([photo_input, select_photo_btn], spacing=10),
        name_input, gender_input, phone_input, bio_input, 
        ft.Row([ft.Container(content=state_input, expand=True), ft.Container(content=township_input, expand=True)], spacing=10),
        curriculum_input, teaching_mode_input,
        ft.Row([ft.Container(content=grade_input1, expand=True), ft.Container(content=subject_input1, expand=True)], spacing=10),
        ft.Row([ft.Container(content=grade_input2, expand=True), ft.Container(content=subject_input2, expand=True)], spacing=10),
        ft.Row([ft.Container(content=grade_input3, expand=True), ft.Container(content=subject_input3, expand=True)], spacing=10),
        ft.Row([ft.Container(content=grade_input4, expand=True), ft.Container(content=subject_input4, expand=True)], spacing=10),
        days_input, time_input, current_time_remark_input, fee_input, ft.Divider(),
        view_mode_buttons, edit_mode_buttons, ft.Divider(),
        ft.Text("✅ အတည်ပြုပြီးမြောက်သော စာသင်စာရင်းများ", size=12, weight="bold", color="green"),
        teacher_completed_students_list, ft.Divider(),
        ft.TextButton("Logout ပြန်ထွက်မည်", on_click=lambda _: [
            setattr(page, 'logged_in_tutor_id', None), 
            setattr(teacher_content_area, 'content', teacher_auth_view), 
            setattr(teacher_nav_row, 'visible', False),      # Menu ပြန်ဖျောက်ရန်
            setattr(teacher_nav_divider, 'visible', False),  # မျဉ်းကြောင်း ပြန်ဖျောက်ရန်
            setattr(register_msg, 'value', ""), 
            page.update()
        ]),
        register_msg
    ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
    teacher_jobs_container = ft.Column([teacher_job_list], expand=True)
    teacher_content_area = ft.Container(content=teacher_auth_view, expand=True)

    def toggle_teacher_view(e):
        val = list(e.control.selected)[0] if e.control.selected else "profile"
        if val == "profile":
            teacher_content_area.content = teacher_profile_view if page.logged_in_tutor_id else teacher_auth_view
            if page.logged_in_tutor_id: set_form_disabled(True); view_mode_buttons.visible = True; edit_mode_buttons.visible = False; load_tutor_profile()
        elif val == "posts":
            teacher_content_area.content = teacher_jobs_container; refresh_teacher_job_view()
        elif val == "chat":
            teacher_content_area.content = teacher_chat_container; refresh_teacher_chat_view()
        page.update()

    teacher_nav_row = ft.Row([
        ft.SegmentedButton(selected=["profile"], segments=[
            ft.Segment(value="profile", label=ft.Text("My Profile")), 
            ft.Segment(value="posts", label=ft.Text("Post များ")),
            ft.Segment(value="chat", label=ft.Text("Admin Chat"))  
        ], on_change=toggle_teacher_view)
    ], alignment=ft.MainAxisAlignment.CENTER, visible=False) # <--- Login ဝင်မှပေါ်ရန် ဖျောက်ထားသည်

    teacher_nav_divider = ft.Divider(visible=False)

    teacher_tab = ft.Column([
        teacher_nav_row, 
        teacher_nav_divider, 
        teacher_content_area
    ], expand=True)

    # =========================================================================
    # --- ၂။ STUDENT TAB ---
    # =========================================================================
    stu_login_user = ft.TextField(label="Student Username", border_color="#d1d9e6", bgcolor="white")
    stu_login_pass = ft.TextField(label="Password", password=True, border_color="#d1d9e6", bgcolor="white")
    stu_login_msg = ft.Text(color="red")

    stu_reg_user = ft.TextField(label="Username (ဥပမာ - MaMa)")
    stu_reg_pass = ft.TextField(label="Password (မိမိဖုန်းနံပါတ် ဥပမာ - 09444433555)", password=True)
    stu_reg_name = ft.TextField(label="ကျောင်းသား/မိဘ အမည်")
    stu_reg_phone = ft.TextField(label="ဆက်သွယ်ရန် ဖုန်းနံပါတ် (ဥပမာ - 09444433555)")
    stu_reg_msg = ft.Text(color="red")

    student_state_filter = ft.Dropdown(label="တိုင်း/ပြည်နယ်", value="အားလုံး", options=[ft.dropdown.Option("အားလုံး")] + [ft.dropdown.Option(s) for s in location_data_states])
    student_township_filter = ft.TextField(label="မြို့နယ်ဖြင့်ရှာရန် (စာဖြင့်ရိုက်ပါ)")
    
    student_state_filter.on_change = lambda e: refresh_student_view()
    student_township_filter.on_change = lambda e: refresh_student_view()

    student_list = ft.ListView(expand=True, spacing=10)

    student_my_posts_list = ft.ListView(expand=False, spacing=10)
    student_completed_tutors_list = ft.ListView(expand=False, spacing=10)
    
    stu_name_in = ft.TextField(label="သင့်အမည် (ကျောင်းသား/မိဘ)", disabled=True)
    stu_phone_in = ft.TextField(label="သင့်ဖုန်းနံပါတ်", disabled=True)
    current_selected_tutor_id = [None]

    def do_stu_login(e):
        res = supabase.table("students").select("id, name, phone").eq("username", stu_login_user.value).eq("password", stu_login_pass.value).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            page.logged_in_student_id = row.get("id")
            page.logged_in_student_name = row.get("name")
            page.logged_in_student_phone = row.get("phone")
            stu_login_msg.value = ""
            
            stu_name_in.value = page.logged_in_student_name
            stu_phone_in.value = page.logged_in_student_phone
            post_stu_name.value = page.logged_in_student_name
            post_stu_phone.value = page.logged_in_student_phone
            
            student_content_area.content = student_main_view
            refresh_student_view()
        else:
            stu_login_msg.value = "Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။"
        page.update()

    def do_stu_register(e):
        u = stu_reg_user.value.strip()
        p = stu_reg_pass.value.strip()
        n = stu_reg_name.value.strip()
        ph = stu_reg_phone.value.strip()
        
        if not u or not p or not n or not ph:
            stu_reg_msg.value = "အချက်အလက်များကို ပြည့်စုံစွာဖြည့်စွက်ပါ။"; stu_reg_msg.color = "red"; page.update(); return
            
        if not re.match(r"^([A-Z][a-z]+)+$", u):
            stu_reg_msg.value = "Username သည် Space မပါဘဲ နာမည်အစစာလုံးတိုင်း UpperCase ဖြစ်ရပါမည် (ဥပမာ - MaMa)။"
            stu_reg_msg.color = "red"; page.update(); return
            
        if p != ph:
            stu_reg_msg.value = "Password သည် ဖုန်းနံပါတ် အတိအကျ ဖြစ်ရပါမည် (ဥပမာ - 09444433555)။"
            stu_reg_msg.color = "red"; page.update(); return
            
        if not re.match(r"^(09|\u1040\u1049)?[0-9\u1040-\u1049]{7,11}$", ph):
            stu_reg_msg.value = "ဖုန်းနံပါတ်/Password သည် တရားဝင် ဖုန်းနံပါတ် ဖြစ်ရပါမည် (ဥပမာ - 09444433555)။"
            stu_reg_msg.color = "red"; page.update(); return
            
        try:
            supabase.table("students").insert({"username": u, "password": p, "name": n, "phone": ph}).execute()
            stu_reg_msg.value = "အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါသည်။ Login ဝင်နိုင်ပါပြီ။"; stu_reg_msg.color = "green"
            stu_reg_user.value = ""; stu_reg_pass.value = ""; stu_reg_name.value = ""; stu_reg_phone.value = ""
        except Exception:
            stu_reg_msg.value = "ဤ Username က ရှိပြီးသား ဖြစ်နေသဖြင့် အခြားပြောင်းပေးပါ။"; stu_reg_msg.color = "red"
        page.update()

    stu_auth_view = ft.Column([
        ft.Text("STUDENT", size=24, weight="bold", color="#1a1a4b"),
        
        # --- Login Card ---
        ft.Container(
            content=ft.Column([
                ft.Text("Student Login", size=16, weight="bold", color="#2196F3"),
                stu_login_user, 
                stu_login_pass, 
                stu_login_msg,
                ft.Row([
                    ft.ElevatedButton(
                        "Login ဝင်မည်", on_click=do_stu_login, width=150, 
                        bgcolor="#F4F6F9", color="#1a1a4b", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#F9FAFE", padding=20, border_radius=10, 
            width=350,
        ),
        
        ft.Container(height=10),
        
        # --- Register Card ---
        ft.Container(
            content=ft.Row([
                ft.Text("အကောင့်မရှိသေးပါက -", size=12, color="grey"), 
                ft.TextButton("Register လုပ်ရန်", on_click=lambda _: [setattr(student_content_area, 'content', stu_reg_view), setattr(stu_reg_msg, 'value', ''), page.update()])
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#F9FAFE", padding=10, border_radius=10,
            width=350,
        )
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    stu_reg_view = ft.Column([
        ft.Text("Student Register", size=18, weight="bold", color="green"),
        stu_reg_user, stu_reg_pass, stu_reg_name, stu_reg_phone, stu_reg_msg,
        ft.Button("Register အကောင့်ဖွင့်မည်", on_click=do_stu_register, width=220),
        ft.Divider(),
        ft.TextButton("Login သို့ ပြန်သွားမည်", on_click=lambda _: [setattr(student_content_area, 'content', stu_auth_view), setattr(stu_login_msg, 'value', ''), page.update()])
    ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

    def submit_direct_request(e):
        if stu_name_in.value and stu_phone_in.value:
            supabase.table("requests").insert({
                "tutor_id": current_selected_tutor_id[0],
                "student_name": stu_name_in.value,
                "student_phone": stu_phone_in.value,
                "status": "pending",
                "reject_reason": ""
            }).execute()
            
            t_res = supabase.table("tutors").select("name, username").eq("id", current_selected_tutor_id[0]).execute()
            t_display = t_res.data[0].get("name") if (t_res.data and t_res.data[0].get("name")) else t_res.data[0].get("username")
            
            add_notification("Direct ချိတ်ဆက်မှုတောင်းဆိုချက်", f"ကျောင်းသား {stu_name_in.value} (ဖုန်း: {stu_phone_in.value}) က ဆရာ {t_display} နှင့် matching ရန် ချိတ်ဆက်မှုပြုလုပ်ထားပါသည်။")
            booking_dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text("ချိတ်ဆက်ပေးရန် Admin ထံ တောင်းဆိုချက် ပို့ပြီးပါပြီ။")); page.snack_bar.open = True
            if page.is_admin_logged_in: refresh_admin_view()
            page.update()

    booking_dialog = ft.AlertDialog(title=ft.Text("ဆရာနှင့် ချိတ်ဆက်ရန် တောင်းဆိုမည်လား"), content=ft.Column([stu_name_in, stu_phone_in], tight=True), actions=[ft.TextButton("တောင်းဆိုမည်", on_click=submit_direct_request)])
    page.overlay.append(booking_dialog)

    def refresh_student_view():
        student_list.controls.clear()
        f_state = student_state_filter.value or "အားလုံး"
        f_town = student_township_filter.value.strip() if student_township_filter.value else ""
        
        res = supabase.table("tutors").select("*").eq("status", "approved").execute()
        for row in res.data:
            t_id = row.get("id")
            t_name = row.get("name")
            t_gen = row.get("gender")
            t_state = row.get("state")
            t_township = row.get("township")
            t_curriculum = row.get("curriculum")
            t_mode = row.get("teaching_mode")
            g1, s1 = row.get("grade1"), row.get("subject1")
            g2, s2 = row.get("grade2"), row.get("subject2")
            g3, s3 = row.get("grade3"), row.get("subject3")
            g4, s4 = row.get("grade4"), row.get("subject4")
            t_days = row.get("days")
            t_time = row.get("time")
            t_fee = row.get("fee")
            t_photo = row.get("photo")
            
            if f_state != "အားလုံး" and t_state != f_state: continue
            if f_town and t_township and f_town not in t_township: continue
            
            sub_txt = f"• {g1} ({s1})\n" if g1 and s1 else ""
            if g2 and s2: sub_txt += f"• {g2} ({s2})\n"
            if g3 and s3: sub_txt += f"• {g3} ({s3})\n"
            if g4 and s4: sub_txt += f"• {g4} ({s4})\n"
            
            card_items = []
            if t_photo:
                card_items.append(ft.Row([ft.Image(src=t_photo, width=80, height=80, fit="cover", border_radius=40)], alignment=ft.MainAxisAlignment.CENTER))
                
            card_items.extend([
                ft.Text(f"အမည်: {t_name} ({t_gen})", weight="bold", size=14),
                ft.Text(f"သင်ရိုးစနစ်: {t_curriculum if t_curriculum else '-'} | သင်ကြားမည့်စနစ်: {t_mode if t_mode else '-'}", color="orange", weight="bold", size=12),
                ft.Text(f"ဒေသ: {t_state}, {t_township}", color="red", size=12), ft.Divider(),
                ft.Text("သင်ကြားနိုင်သည့် အတန်းနှင့် ဘာသာရပ်များ-", size=11, weight="bold"), ft.Text(sub_txt.strip() if sub_txt else "မရှိပါ", size=11),
                ft.Text(f"ရက်/အချိန်: {t_days} ({t_time})", size=11), ft.Text(f"လစဉ်ကြေး: {t_fee} Ks", color="green", weight="bold", size=13),
                ft.Button(content=ft.Row([ft.Icon(ft.Icons.PHONE), ft.Text("ဒီဆရာနဲ့ သင်မယ် (Admin ထံတောင်းဆိုရန်)")], tight=True), on_click=lambda e, tid=t_id: [current_selected_tutor_id.__setitem__(0, tid), setattr(booking_dialog, 'open', True), page.update()])
            ])

            student_list.controls.append(ft.Card(content=ft.Container(padding=12, content=ft.Column(card_items))))
        if not student_list.controls: student_list.controls.append(ft.Text("ဤဒေသတွင် ဆရာမရှိသေးပါ။"))
        page.update()

    def refresh_student_my_posts():
        student_my_posts_list.controls.clear()
        student_completed_tutors_list.controls.clear() # <- ဒီနေရာလေး ကျန်ခဲ့တာပါ
        if not page.logged_in_student_name: return
        
        # (၁) Pending/Active ဖြစ်နေသော ပို့စ်များ
        posts_res = supabase.table("job_posts").select("*").eq("stu_name", page.logged_in_student_name).eq("stu_phone", page.logged_in_student_phone).neq("status", "completed").execute()
        posts = posts_res.data
        
        if not posts:
            student_my_posts_list.controls.append(ft.Text("သင်တင်ထားသော Active Post မရှိသေးပါ။", color="grey", size=12))
        else:
            for p in posts:
                j_id = p.get("id"); subj = p.get("subject"); p_state = p.get("state")
                town = p.get("township"); fee = p.get("fee_offer"); details = p.get("details"); stat = p.get("status")
                
                app_res = supabase.table("job_applications").select("id", count="exact").eq("job_id", j_id).execute()
                app_count = app_res.count if app_res.count is not None else len(app_res.data)
                
                status_text = "အတည်ပြုချက်စောင့်ဆိုင်းဆဲ" if stat == 'pending' else "ဆရာများ လျှောက်ထားနိုင်ပါပြီ"
                status_color = "orange" if stat == 'pending' else "green"
                
                student_my_posts_list.controls.append(ft.Card(content=ft.Container(padding=12, content=ft.Column([
                    ft.Text(f"ဘာသာရပ်: {subj}", weight="bold", size=14, color="blue"),
                    ft.Text(f"ဒေသ: {p_state}, {town} | နှုန်းထား: {fee} Ks", size=12),
                    ft.Text(f"အသေးစိတ်: {details}", size=12),
                    ft.Divider(),
                    ft.Text(f"အခြေအနေ: {status_text}", color=status_color, size=11, weight="bold"),
                    ft.Text(f"👨‍🏫 လျှောက်ထားသော ဆရာအရေအတွက်: {app_count} ယောက်", color="teal", size=12, weight="bold")
                ]))))

        # (၂) ချိတ်ဆက်ပြီးမြောက်သွားသော ဆရာများစာရင်း (Admin မှ ရွေးချယ်ပေးလိုက်သူများ)
        c_res = supabase.table("requests").select("*, tutors(*)").eq("student_phone", page.logged_in_student_phone).eq("status", "completed").execute()
        for row in c_res.data:
            t_info = row.get("tutors") or {}
            t_name = t_info.get("name") if t_info.get("name") else t_info.get("username", "Unknown")
            t_phone = t_info.get("phone", "-")
            student_completed_tutors_list.controls.append(ft.Card(content=ft.Container(padding=12, content=ft.Column([
                ft.Text(f"🎉 ချိတ်ဆက်ပြီးမြောက်သော ဆရာ: {t_name}", color="green", weight="bold"),
                ft.Text(f"📞 ဆက်သွယ်ရန်ဖုန်း: {t_phone}", size=13),
                ft.Text("Admin မှ ဤဆရာနှင့် ချိတ်ဆက်ပေးလိုက်ပါပြီ။", size=11, color="grey")
            ]))))
            
        if not student_completed_tutors_list.controls:
            student_completed_tutors_list.controls.append(ft.Text("ချိတ်ဆက်ပြီးမြောက်ထားသော ဆရာမရှိသေးပါ။", color="grey", size=12))
            
        page.update()

    post_stu_name = ft.TextField(label="ကျောင်းသား/မိဘ အမည်", disabled=True)
    post_stu_phone = ft.TextField(label="ဆက်သွယ်ရန် ဖုန်းနံပါတ်", disabled=True)
    post_subject = ft.TextField(label="လိုချင်သော ဘာသာရပ်/အတန်း")
    
    post_state = ft.Dropdown(label="တိုင်း/ပြည်နယ်", options=[ft.dropdown.Option(s) for s in location_data_states])
    post_township = ft.TextField(label="မြို့နယ် (စာဖြင့်ရိုက်ပါ)")
    
    post_fee = ft.TextField(label="ပေးနိုင်သော လစဉ်ကြေးနှုန်းထား")
    post_details = ft.TextField(label="အသေးစိတ်အချက်အလက်", multiline=True)
    post_msg = ft.Text(color="green")

    def submit_job_post(e):
        if not post_stu_name.value or not post_stu_phone.value or not post_subject.value or not post_state.value or not post_township.value:
            post_msg.value = "လိုအပ်ချက်များ ဖြည့်စွက်ပါ။"; post_msg.color = "red"; page.update(); return
        
        supabase.table("job_posts").insert({
            "stu_name": post_stu_name.value, "stu_phone": post_stu_phone.value, "subject": post_subject.value,
            "state": post_state.value, "township": post_township.value, "fee_offer": post_fee.value,
            "details": post_details.value, "status": "pending", "reject_reason": ""
        }).execute()
        
        add_notification("ဆရာခေါ်စာအသစ် ရောက်ရှိလာခြင်း", f"မိဘ {post_stu_name.value} က ဘာသာရပ် [{post_subject.value}] အတွက် ဆရာခေါ်ယူရန် ပို့စ်အသစ်တစ်ခု တင်လိုက်ပါသည်။")
        post_msg.value = "ဆရာခေါ်စာ တင်ပြီးပါပြီ။ Admin အတည်ပြုချက်စောင့်ပါ။"; post_msg.color = "green"
        post_subject.value = ""; post_state.value = None; post_township.value = ""; post_fee.value = ""; post_details.value = ""
        page.update()

    student_search_view = ft.Column([
        ft.Row([ft.Container(content=student_state_filter, expand=True), ft.Container(content=student_township_filter, expand=True)], spacing=10), 
        student_list
    ], expand=True)
    
    student_post_view = ft.Column([
        post_stu_name, post_stu_phone, post_subject, 
        ft.Row([ft.Container(content=post_state, expand=True), ft.Container(content=post_township, expand=True)], spacing=10),
        post_fee, post_details, 
        ft.Button(content=ft.Row([ft.Icon(ft.Icons.ADD), ft.Text("Post တင်မည်")], tight=True), on_click=submit_job_post), 
        post_msg
    ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)
    
    student_my_posts_view = ft.Column([
        ft.Text("စောင့်ဆိုင်းဆဲ / လျှောက်ထားဆဲ Post များ", weight="bold", color="blue", size=13),
        student_my_posts_list,
        ft.Divider(),
        ft.Text("✅ အောင်မြင်စွာ ချိတ်ဆက်ပြီးသော စာရင်း", weight="bold", color="green", size=13),
        student_completed_tutors_list
    ], expand=True, scroll=ft.ScrollMode.AUTO)
    
    student_subcontent_area = ft.Container(content=student_search_view, expand=True)

    def toggle_student_subview(e):
        val = list(e.control.selected)[0] if e.control.selected else "search"
        if val == "search": 
            student_subcontent_area.content = student_search_view; refresh_student_view()
        elif val == "post": 
            student_subcontent_area.content = student_post_view
        elif val == "my_posts": 
            student_subcontent_area.content = student_my_posts_view; refresh_student_my_posts()
        page.update()

    def logout_student():
        page.logged_in_student_id = None
        page.logged_in_student_name = ""
        page.logged_in_student_phone = ""
        student_content_area.content = stu_auth_view
        stu_login_user.value = ""; stu_login_pass.value = ""
        page.update()

    student_main_view = ft.Column([
        ft.Row([
            ft.SegmentedButton(selected=["search"], segments=[
                ft.Segment(value="search", label=ft.Text("ဆရာရှာရန်")), 
                ft.Segment(value="post", label=ft.Text("Post တင်ရန်")),
                ft.Segment(value="my_posts", label=ft.Text("မိမိ၏ Post များ"))
            ], on_change=toggle_student_subview),
            ft.IconButton(ft.Icons.LOGOUT, icon_color="red", on_click=lambda _: logout_student(), tooltip="Logout ထွက်မည်")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(), student_subcontent_area
    ], expand=True)

    student_content_area = ft.Container(content=stu_auth_view, expand=True)
    
    student_tab = ft.Column([
        student_content_area
    ], expand=True)


    # =========================================================================
    # --- ၄။ ADMIN TAB ---
    # =========================================================================
    admin_pass_input = ft.TextField(label="Admin Password", password=True)
    admin_pending_list = ft.ListView(spacing=10, expand=True)
    admin_approved_list = ft.ListView(spacing=10, expand=True) 
    
    admin_posts_pending_list = ft.ListView(spacing=10, expand=True)
    admin_posts_approved_list = ft.ListView(spacing=10, expand=True)
    admin_posts_completed_list = ft.ListView(spacing=10, expand=True)
    
    admin_direct_pending_area = ft.ListView(spacing=5, expand=True)
    admin_direct_completed_area = ft.ListView(spacing=5, expand=True)
    admin_notification_list = ft.ListView(spacing=8, expand=True) 
    
    admin_chat_tutors_list = ft.ListView(spacing=5, expand=True) 
    admin_chat_box_list = ft.ListView(spacing=5, expand=True, auto_scroll=True) 
    admin_chat_input = ft.TextField(label="ဆရာ့ထံ စာပြန်ရန်...", expand=True)
    admin_chat_right_panel = ft.Column(visible=False, expand=True) 


    # --- Password Reset Dialog ---
    reset_target_tutor_id = [None]
    new_password_field = ft.TextField(label="Password အသစ် သတ်မှတ်ပေးပါ")
    
    def execute_password_reset(e):
        if not new_password_field.value: return
        supabase.table("tutors").update({"password": new_password_field.value}).eq("id", reset_target_tutor_id[0]).execute()
        reset_dialog.open = False; new_password_field.value = ""
        page.snack_bar = ft.SnackBar(ft.Text("ဆရာ့ Password အား Reset ပြောင်းလဲပေးပြီးပါပြီ။")); page.snack_bar.open = True
        refresh_admin_view(); page.update()

    reset_dialog = ft.AlertDialog(title=ft.Text("Password ပြန်သတ်မှတ်ရန်"), content=new_password_field, actions=[ft.ElevatedButton("သိမ်းဆည်းမည်", on_click=execute_password_reset, bgcolor="green", color="white")])
    page.overlay.append(reset_dialog)

    # --- Reject Reason Dialog ---
    reject_target_id = [None]; reject_target_type = ["tutor"] 
    reason_field = ft.TextField(label="ငြင်းပယ်ရသည့် အကြောင်းရင်း (Reason)")

    def execute_reject(e):
        if not reason_field.value: return
        if reject_target_type[0] == "tutor": 
            supabase.table("tutors").update({"status": "rejected", "reject_reason": reason_field.value}).eq("id", reject_target_id[0]).execute()
        else: 
            supabase.table("job_posts").update({"status": "rejected", "reject_reason": reason_field.value}).eq("id", reject_target_id[0]).execute()
        
        reject_dialog.open = False; reason_field.value = ""; detail_dialog.open = False 
        refresh_admin_view(); page.update()

    reject_dialog = ft.AlertDialog(title=ft.Text("Reject အကြောင်းရင်း ဖြည့်ပါ"), content=reason_field, actions=[ft.TextButton("Reject လုပ်မည်", on_click=execute_reject)])
    page.overlay.append(reject_dialog)

    # --- Blacklist Dialog ---
    blacklist_target_id = [None]
    blacklist_reason_field = ft.TextField(label="Black List သွင်းရသည့် အကြောင်းရင်း")

    def execute_blacklist(e):
        if not blacklist_reason_field.value: return
        supabase.table("tutors").update({"status": "blacklisted", "reject_reason": blacklist_reason_field.value}).eq("id", blacklist_target_id[0]).execute()
        add_notification("Black List စာရင်းသွင်းခြင်း", f"ဆရာအကောင့်တစ်ခုအား Black List သို့ ပြောင်းရွှေ့လိုက်ပါသည်။")
        blacklist_dialog.open = False
        blacklist_reason_field.value = ""
        refresh_admin_view()
        if main_container.content == blacklist_tab: refresh_blacklist_view()
        page.update()

    blacklist_dialog = ft.AlertDialog(
        title=ft.Text("Black List သွင်းရန်"),
        content=blacklist_reason_field,
        actions=[ft.ElevatedButton("အတည်ပြုမည်", on_click=execute_blacklist, bgcolor="black", color="white")]
    )
    page.overlay.append(blacklist_dialog)

    direct_reject_target_id = [None]
    direct_reject_reason_field = ft.TextField(label="ချိတ်ဆက်မှုအား ငြင်းပယ်ရသည့် အကြောင်းရင်း")

    def execute_direct_request_reject(e):
        if not direct_reject_reason_field.value: return
        supabase.table("requests").update({"status": "rejected", "reject_reason": direct_reject_reason_field.value}).eq("id", direct_reject_target_id[0]).execute()
        
        r_res = supabase.table("requests").select("student_name").eq("id", direct_reject_target_id[0]).execute()
        s_name = r_res.data[0].get("student_name") if r_res.data else "Unknown"
        
        add_notification("ချိတ်ဆက်မှု ငြင်းပယ်ခြင်း", f"ကျောင်းသား {s_name} နှင့် ဆရာတို့၏ ချိတ်ဆက်မှုတောင်းဆိုချက်အား Admin မှ ငြင်းပယ်လိုက်ပါသည်။ (အကြောင်းရင်း: {direct_reject_reason_field.value})")
        
        direct_reject_dialog.open = False; direct_reject_reason_field.value = ""
        direct_detail_dialog.open = False 
        refresh_admin_view(); page.update()

    direct_reject_dialog = ft.AlertDialog(
        title=ft.Text("ချိတ်ဆက်မှု ငြင်းပယ်ရန် အကြောင်းရင်းဖြည့်စွက်ပါ"),
        content=direct_reject_reason_field,
        actions=[ft.ElevatedButton("ငြင်းပယ်မှုကို အတည်ပြုမည်", on_click=execute_direct_request_reject, bgcolor="red", color="white")]
    )
    page.overlay.append(direct_reject_dialog)

    detail_content = ft.Column(tight=True, scroll=ft.ScrollMode.AUTO, height=450, spacing=8)
    detail_dialog = ft.AlertDialog(title=ft.Text("ဆရာ/မ အသေးစိတ် ကိုယ်ရေးရာဇဝင်"), content=ft.Container(content=detail_content, width=360), actions_alignment=ft.MainAxisAlignment.SPACE_EVENLY)
    page.overlay.append(detail_dialog)

    direct_detail_content = ft.Column(expand=False, scroll=ft.ScrollMode.AUTO, height=450, spacing=8)
    direct_detail_dialog = ft.AlertDialog(title=ft.Text("ချိတ်ဆက်မှု အချက်အလက်စုံလင်စွာကြည့်ရှုခြင်း"), content=ft.Container(content=direct_detail_content, width=360))
    page.overlay.append(direct_detail_dialog)

    # =========================================================
    # လျှောက်ထားသော ဆရာများစာရင်းပြရန် Dialog
    # =========================================================
    applicants_list_content = ft.Column(scroll=ft.ScrollMode.AUTO, height=400, spacing=10)
    applicants_list_dialog = ft.AlertDialog(
        title=ft.Text("လျှောက်ထားသော ဆရာ/မ များစာရင်း", size=16, weight="bold"),
        content=ft.Container(content=applicants_list_content, width=350),
        actions=[ft.TextButton("ပိတ်မည်", on_click=lambda _: [setattr(applicants_list_dialog, 'open', False), page.update()])]
    )
    page.overlay.append(applicants_list_dialog)

    # Admin က ဆရာကို ရွေးချယ်ပြီး Done နှိပ်လိုက်သောအခါ အလုပ်လုပ်မည့် Function
    def hire_tutor_for_job(tutor_id, job_id, stu_name, stu_phone):
        # ၁။ Job Post ကို Completed အဖြစ် ပြောင်းမည်
        supabase.table("job_posts").update({"status": "completed"}).eq("id", job_id).execute()
        # ၂။ Requests Table ထဲသို့ မှတ်တမ်းထည့်မည် (Teacher/Student တွေမြင်ရအောင်)
        supabase.table("requests").insert({
            "tutor_id": tutor_id,
            "student_name": stu_name,
            "student_phone": stu_phone,
            "status": "completed",
            "reject_reason": "Post မှတဆင့် ချိတ်ဆက်ပေးခြင်း"
        }).execute()
        
        applicants_list_dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text("ကျောင်းသားနှင့် ဆရာ ချိတ်ဆက်မှု အောင်မြင်စွာ ပြီးမြောက်ပါပြီ။"))
        page.snack_bar.open = True
        refresh_admin_view()
        page.update()

    def open_applicants_list_popup(job_id, job_subject, stu_name, stu_phone):
        applicants_list_content.controls.clear()
        applicants_list_content.controls.append(ft.Text(f"လိုအပ်သောဘာသာရပ်: {job_subject}", color="blue", weight="bold"))
        applicants_list_content.controls.append(ft.Divider())

        apps = supabase.table("job_applications").select("*, tutors(*)").eq("job_id", job_id).execute()

        if not apps.data:
            applicants_list_content.controls.append(ft.Text("လျှောက်ထားသူ မရှိသေးပါ။", color="grey", size=12))
        else:
            for item in apps.data:
                t_info = item.get("tutors") or {}
                t_id = t_info.get("id")
                t_name = t_info.get("name")
                u_name = t_info.get("username")
                t_phone = t_info.get("phone")
                applied_time = item.get("timestamp")

                display_name = t_name if t_name else f"{u_name} (Profile မဖြည့်ရသေးပါ)"
                applicants_list_content.controls.append(
                    ft.Card(content=ft.Container(padding=10, content=ft.Column([
                        ft.Text(f"👨‍🏫 ဆရာ/မ: {display_name}", weight="bold", size=13),
                        ft.Text(f"📞 ဖုန်း: {t_phone if t_phone else '-'}", size=12),
                        
                        ft.Row([
                            ft.ElevatedButton("Detail", icon=ft.Icons.PERSON, on_click=lambda e, tid=t_id: open_tutor_detail_popup(tid, view_only=True), bgcolor="teal", color="white"),
                            # --- [အသစ်ထည့်လိုက်သော ခလုတ် (ဆရာရွေးရန်)] ---
                            ft.ElevatedButton("ချိတ်ဆက်ပေးမည် (Done)", icon=ft.Icons.HANDSHAKE, on_click=lambda e, tid=t_id, jid=job_id, sn=stu_name, sp=stu_phone: hire_tutor_for_job(tid, jid, sn, sp), bgcolor="green", color="white")
                        ], wrap=True)
                    ])))
                )

        applicants_list_dialog.open = True
        page.update()

    def open_direct_request_detail_popup(request_id):
        res = supabase.table("requests").select("*, tutors(*)").eq("id", request_id).execute()
        if not res.data: return
        
        row = res.data[0]
        s_name = row.get("student_name")
        s_phone = row.get("student_phone")
        t_info = row.get("tutors") or {}
        
        t_name = t_info.get("name"); t_gen = t_info.get("gender"); t_phone = t_info.get("phone")
        t_bio = t_info.get("bio"); t_state = t_info.get("state"); t_town = t_info.get("township")
        t_curr = t_info.get("curriculum"); t_mode = t_info.get("teaching_mode")
        g1, s1 = t_info.get("grade1"), t_info.get("subject1")
        g2, s2 = t_info.get("grade2"), t_info.get("subject2")
        g3, s3 = t_info.get("grade3"), t_info.get("subject3")
        g4, s4 = t_info.get("grade4"), t_info.get("subject4")
        t_days = t_info.get("days"); t_time = t_info.get("time"); t_fee = t_info.get("fee"); t_photo = t_info.get("photo")
        
        sub_txt = f"• {g1} ({s1})\n" if g1 and s1 else ""
        if g2 and s2: sub_txt += f"• {g2} ({s2})\n"
        if g3 and s3: sub_txt += f"• {g3} ({s3})\n"
        if g4 and s4: sub_txt += f"• {g4} ({s4})\n"

        popup_items = []
        if t_photo:
            popup_items.append(ft.Row([ft.Image(src=t_photo, width=100, height=100, fit="cover", border_radius=50)], alignment=ft.MainAxisAlignment.CENTER))

        popup_items.extend([
            ft.Text("📋 လျှောက်ထားသူ ကျောင်းသား/မိဘ အချက်အလက်", weight="bold", color="blue", size=14),
            ft.Text(f"အမည်: {s_name}"), ft.Text(f"ဖုန်းနံပါတ်: {s_phone}", color="green", weight="bold"), ft.Divider(),
            ft.Text("👨‍🏫 အချိတ်ဆက်ခံရသူ ဆရာ/မ ကိုယ်ရေးရာဇဝင်", weight="bold", color="orange", size=14),
            ft.Text(f"အမည်: {t_name if t_name else '-'} ({t_gen if t_gen else '-'})"),
            ft.Text(f"ဆရာ့ဖုန်းနံပါတ်: {t_phone if t_phone else '-'}", color="green"),
            ft.Text(f"ဒေသ: {t_state if t_state else '-'}, {t_town if t_town else '-'} | သင်ရိုး: {t_curr if t_curr else '-'} | စနစ်: {t_mode if t_mode else '-'}" ),
            ft.Text(f"ကိုယ်ရေးအကျဉ်း: {t_bio if t_bio else '-'}", italic=True, size=12), ft.Divider(),
            ft.Text("သင်ကြားမည့် အတန်း/ဘာသာရပ်များ-", size=12, weight="bold"), ft.Text(sub_txt.strip() if sub_txt else "-", size=12), ft.Divider(),
            ft.Text(f"သင်ကြားမည့်ရက်/အချိန်: {t_days if t_days else '-'} ({t_time if t_time else '-'})", size=12),
            ft.Text(f"တောင်းဆိုသောလစဉ်ကြေး: {t_fee if t_fee else '-'} Ks", size=14, weight="bold", color="green"),
        ])

        direct_detail_content.controls = popup_items
        
        direct_detail_dialog.actions = [
            ft.ElevatedButton("ချိတ်ဆက်မည်", icon=ft.Icons.CHECK, bgcolor="green", color="white",
                              on_click=lambda e, rid=request_id: [supabase.table("requests").update({"status": "completed"}).eq("id", rid).execute(), setattr(direct_detail_dialog, 'open', False), refresh_admin_view()]),
            ft.ElevatedButton("ငြင်းပယ်မည်", icon=ft.Icons.CLOSE, bgcolor="red", color="white",
                              on_click=lambda e, rid=request_id: [direct_reject_target_id.__setitem__(0, rid), setattr(direct_reject_dialog, 'open', True), page.update()]),
            ft.TextButton("ပိတ်မည်", on_click=lambda _: [setattr(direct_detail_dialog, 'open', False), page.update()])
        ]
        direct_detail_dialog.open = True
        page.update()

    def open_tutor_detail_popup(tutor_id, view_only=False):
        res = supabase.table("tutors").select("*").eq("id", tutor_id).execute()
        if not res.data: return
        row = res.data[0]
        
        u_name = row.get("username"); u_pass = row.get("password"); t_name = row.get("name"); t_gen = row.get("gender")
        t_phone = row.get("phone"); t_bio = row.get("bio"); t_state = row.get("state"); t_town = row.get("township")
        t_curr = row.get("curriculum"); t_mode = row.get("teaching_mode")
        g1, s1 = row.get("grade1"), row.get("subject1")
        g2, s2 = row.get("grade2"), row.get("subject2")
        g3, s3 = row.get("grade3"), row.get("subject3")
        g4, s4 = row.get("grade4"), row.get("subject4")
        t_days = row.get("days"); t_time = row.get("time"); t_rem = row.get("current_time_remark"); t_fee = row.get("fee"); t_photo = row.get("photo")
        
        sub_txt = f"• {g1} ({s1})\n" if g1 and s1 else ""
        if g2 and s2: sub_txt += f"• {g2} ({s2})\n"
        if g3 and s3: sub_txt += f"• {g3} ({s3})\n"
        if g4 and s4: sub_txt += f"• {g4} ({s4})\n"

        popup_items = []
        if t_photo:
            popup_items.append(ft.Row([ft.Image(src=t_photo, width=100, height=100, fit="cover", border_radius=50)], alignment=ft.MainAxisAlignment.CENTER))

        popup_items.extend([
            ft.Text(f"Account Username: {u_name}", weight="bold", color="blue"), ft.Text(f"Account Password: {u_pass}", size=12, color="grey"), ft.Divider(),
            ft.Text(f"အမည်: {t_name if t_name else '-'}", size=14, weight="bold"), ft.Text(f"ကျား/မ: {t_gen if t_gen else '-'}", size=13),
            ft.Text(f"ဆက်သွယ်ရန်ဖုန်း: {t_phone if t_phone else '-'}", size=13, color="green", weight="bold"), 
            ft.Text(f"ဒေသ: {t_state if t_state else '-'}, {t_town if t_town else '-'}", size=13),
            ft.Text(f"သင်ရိုးစနစ်: {t_curr if t_curr else '-'} | သင်ကြားမည့်စနစ်: {t_mode if t_mode else '-'}", size=13, color="orange"), 
            ft.Text(f"ကိုယ်ရေးအကျဉ်း: {t_bio if t_bio else '-'}", size=12, italic=True), ft.Divider(),
            ft.Text("သင်ကြားနိုင်သည့် အတန်း/ဘာသာရပ်များ-", size=12, weight="bold"), ft.Text(sub_txt.strip() if sub_txt else "ဖြည့်စွက်ထားခြင်းမရှိပါ", size=12), ft.Divider(),
            ft.Text(f"သင်ကြားမည့်ရက်: {t_days if t_days else '-'}", size=12), ft.Text(f"သင်ကြားမည့်အချိန်: {t_time if t_time else '-'}", size=12),
            ft.Text(f"အချိန်မှတ်ချက်: {t_rem if t_rem else '-'}", size=12, color="blue"), ft.Text(f"တောင်းဆိုသော လစဉ်ကြေး: {t_fee if t_fee else '-'} Ks", size=14, weight="bold", color="green"),
        ])

        detail_content.controls = popup_items
        
        if view_only:
            detail_content.controls.append(ft.Divider())
            detail_content.controls.append(ft.Text("🎉 ဤဆရာနှင့် ချိတ်ဆက်ပြီးမြောက်ခဲ့သော ကျောင်းသားများ-", size=12, weight="bold", color="green"))
            c_res = supabase.table("requests").select("student_name, student_phone").eq("tutor_id", tutor_id).eq("status", "completed").execute()
            for r in c_res.data:
                detail_content.controls.append(ft.Text(f"• {r.get('student_name')} (ဖုန်း: {r.get('student_phone')})", size=12, weight="bold"))
            if not c_res.data:
                detail_content.controls.append(ft.Text("• ချိတ်ဆက်မှုစာရင်း မရှိသေးပါ။", size=12, color="grey"))
            
            detail_dialog.actions = [ft.TextButton("ပိတ်မည်", on_click=lambda _: [setattr(detail_dialog, 'open', False), page.update()])]
        else:
            detail_dialog.actions = [
                ft.ElevatedButton("ခွင့်ပြုမည်", icon=ft.Icons.CHECK, bgcolor="green", color="white", on_click=lambda e, tid=tutor_id: [supabase.table("tutors").update({"status": "approved"}).eq("id", tid).execute(), detail_dialog.__setattr__('open', False), refresh_admin_view()]),
                ft.ElevatedButton("Reject လုပ်မည်", icon=ft.Icons.CLOSE, bgcolor="red", color="white", on_click=lambda e, tid=tutor_id: [reject_target_id.__setitem__(0, tid), reject_target_type.__setitem__(0, "tutor"), setattr(reject_dialog, 'open', True), page.update()]),
                ft.TextButton("ပိတ်မည်", on_click=lambda _: [setattr(detail_dialog, 'open', False), page.update()])
            ]
        detail_dialog.open = True; page.update()

    def send_admin_message(e):
        if not admin_chat_input.value or page.admin_selected_chat_tutor_id is None: return
        supabase.table("chat_messages").insert({
            "tutor_id": page.admin_selected_chat_tutor_id,
            "sender": "admin",
            "message": admin_chat_input.value,
            "image_data": None
        }).execute()
        admin_chat_input.value = ""
        open_chat_with_teacher(page.admin_selected_chat_tutor_id); refresh_teacher_chat_view()

    def open_chat_with_teacher(tutor_id):
        page.admin_selected_chat_tutor_id = tutor_id
        admin_chat_box_list.controls.clear()
        
        t_res = supabase.table("tutors").select("name, username").eq("id", tutor_id).execute()
        display_name = t_res.data[0].get("name") if (t_res.data and t_res.data[0].get("name")) else t_res.data[0].get("username")
        
        admin_chat_right_panel.controls.clear()
        admin_chat_right_panel.controls.extend([
            ft.Text(f"Chat with: {display_name}", weight="bold", color="green"), admin_chat_box_list,
            ft.Row([
                admin_chat_input, 
                ft.IconButton(ft.Icons.IMAGE, icon_color="blue", on_click=lambda _: select_and_send_image("admin")),
                ft.IconButton(ft.Icons.SEND, on_click=send_admin_message)
            ])
        ])
        admin_chat_right_panel.visible = True
        
        c_res = supabase.table("chat_messages").select("*").eq("tutor_id", tutor_id).order("timestamp").execute()
        for row in c_res.data:
            sender = row.get("sender")
            msg = row.get("message")
            img_data = row.get("image_data")
            
            align = ft.MainAxisAlignment.END if sender == "admin" else ft.MainAxisAlignment.START
            color = "#D2F7D2" if sender == "admin" else "#EAEAEA"
            prefix = "Me: " if sender == "admin" else f"{display_name}: "
            
            if img_data:
                content_ui = ft.Column([
                    ft.Text(f"{prefix} ပုံပို့ထားပါသည်", size=10, color="grey"),
                    ft.Image(src=img_data, width=150, height=150, fit="cover", border_radius=5)
                ])
            else:
                content_ui = ft.Text(f"{prefix}{msg}", size=13)
                
            admin_chat_box_list.controls.append(ft.Row([ft.Container(content=content_ui, bgcolor=color, padding=8, border_radius=10)], alignment=align))
        page.update()

    def refresh_admin_chat_view():
        admin_chat_tutors_list.controls.clear()
        c_res = supabase.table("chat_messages").select("tutor_id, tutors(name, username)").execute()
        
        visited_tutors = set()
        for row in c_res.data:
            tid = row.get("tutor_id")
            if tid not in visited_tutors:
                visited_tutors.add(tid)
                t_info = row.get("tutors") or {}
                t_name = t_info.get("name")
                u_name = t_info.get("username")
                admin_chat_tutors_list.controls.append(ft.ListTile(title=ft.Text(f"💬 {t_name if t_name else u_name}", size=13, weight="bold"), on_click=lambda e, id_val=tid: open_chat_with_teacher(id_val)))
        if not admin_chat_tutors_list.controls: admin_chat_tutors_list.controls.append(ft.Text("စာပို့ထားသော ဆရာမရှိသေးပါ။", color="grey", size=12))
        page.update()

    def refresh_admin_notifications():
        admin_notification_list.controls.clear()
        n_res = supabase.table("notifications").select("*").order("timestamp", desc=True).execute()
        for row in n_res.data:
            admin_notification_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.NOTIFICATIONS, color="orange", size=16), ft.Text(row.get("title"), weight="bold", size=13, color="blue")]),
                ft.Text(row.get("message"), size=12),
                ft.Text(f"အချိန်: {row.get('timestamp')}", size=10, color="grey")
            ]))))
        if not admin_notification_list.controls:
            admin_notification_list.controls.append(ft.Text("အကြောင်းကြားစာ (Notification) မရှိသေးပါ။", size=12, color="grey"))
        page.update()

    def refresh_admin_view():
        admin_pending_list.controls.clear(); admin_approved_list.controls.clear()
        admin_posts_pending_list.controls.clear(); admin_posts_approved_list.controls.clear(); admin_posts_completed_list.controls.clear()
        admin_direct_pending_area.controls.clear(); admin_direct_completed_area.controls.clear()
        
        # Tutors Status
        t_res = supabase.table("tutors").select("*").execute()
        for row in t_res.data:
            t_id = row.get("id"); u_name = row.get("username"); u_pass = row.get("password")
            t_name = row.get("name"); t_gen = row.get("gender"); t_phone = row.get("phone")
            t_state = row.get("state"); t_town = row.get("township"); g1 = row.get("grade1"); s1 = row.get("subject1")
            t_stat = row.get("status")

            if t_name is None: detail_txt = f"[အကောင့်သစ် - Profile မဖြည့်ရသေး]\nAcc User: {u_name} | Pass: {u_pass}"
            else: detail_txt = f"Acc User: {u_name} | Pass: {u_pass}\nဆရာ: {t_name} ({t_gen}) | ဖုန်း: {t_phone}\nဒေသ: {t_state}, {t_town} | အတန်း: {g1} ({s1})"
                
            if t_stat == "pending":
                admin_pending_list.controls.append(ft.Card(content=ft.Container(padding=12, content=ft.Column([
                    ft.Text(detail_txt, size=12),
                    ft.Row([ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.REMOVE_RED_EYE, size=14), ft.Text("Detail ဝင်ကြည့်မည်", size=11)], tight=True), on_click=lambda e, tid=t_id: open_tutor_detail_popup(tid, view_only=False), bgcolor="blue", color="white")], alignment=ft.MainAxisAlignment.END)
                ]))))
            elif t_stat == "approved":
                if t_name is not None:
                    admin_approved_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                        ft.Text(f"ဆရာအမည်: {t_name} ({t_gen})", weight="bold", size=13),
                        ft.Text(f"🔐 User: {u_name} | Pass: {u_pass}", color="orange", weight="bold", size=12),
                        ft.Text(f"📞 ဖုန်း: {t_phone} | ဒေသ: {t_state}, {t_town}", size=12),
                        ft.Row([
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.LOCK_RESET, size=14), ft.Text("Reset", size=11)], tight=True), on_click=lambda e, tid=t_id: [reset_target_tutor_id.__setitem__(0, tid), setattr(reset_dialog, 'open', True), page.update()], bgcolor="orange", color="white"),
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.REMOVE_RED_EYE, size=14), ft.Text("Detail", size=11)], tight=True), on_click=lambda e, tid=t_id: open_tutor_detail_popup(tid, view_only=True), bgcolor="blue", color="white"),
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.BLOCK, size=14), ft.Text("Blacklist", size=11)], tight=True), on_click=lambda e, tid=t_id: [blacklist_target_id.__setitem__(0, tid), setattr(blacklist_dialog, 'open', True), page.update()], bgcolor="black", color="white")
                        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, wrap=True)
                    ]))))
                else:
                    admin_approved_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                        ft.Text(f"• User: {u_name} (Profile မဖြည့်ရသေးပါ)", color="grey", size=12),
                        ft.Text(f"🔐 Pass: {u_pass}", color="orange", size=12),
                        ft.Row([
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.LOCK_RESET, size=14), ft.Text("Reset Password", size=11)], tight=True), on_click=lambda e, tid=t_id: [reset_target_tutor_id.__setitem__(0, tid), setattr(reset_dialog, 'open', True), page.update()], bgcolor="orange", color="white"),
                            ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.BLOCK, size=14), ft.Text("Blacklist", size=11)], tight=True), on_click=lambda e, tid=t_id: [blacklist_target_id.__setitem__(0, tid), setattr(blacklist_dialog, 'open', True), page.update()], bgcolor="black", color="white")
                        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, wrap=True)
                    ]))))
                    
        if not admin_approved_list.controls: admin_approved_list.controls.append(ft.Text("Approved ဖြစ်ထားသော ဆရာ/မ မရှိသေးပါ။", size=12, color="grey"))

        # Direct Requests Pending
        req_res = supabase.table("requests").select("*, tutors(name)").eq("status", "pending").execute()
        for row in req_res.data:
            r_id = row.get("id"); s_name = row.get("student_name"); s_phone = row.get("student_phone")
            t_info = row.get("tutors") or {}
            t_name = t_info.get("name")
            req_details = f"ကျောင်းသား: {s_name}\nဖုန်း: {s_phone}\nဆရာ: {t_name if t_name else 'No Name'}"
            admin_direct_pending_area.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Text(req_details, size=11, color="blue", weight="bold"),
                ft.Row([
                    ft.ElevatedButton(content=ft.Row([ft.Icon(ft.Icons.REMOVE_RED_EYE, size=12), ft.Text("Detail", size=10)], tight=True), on_click=lambda e, rid=r_id: open_direct_request_detail_popup(rid), bgcolor="teal", color="white")
                ], alignment=ft.MainAxisAlignment.END)
            ]))))
        if not admin_direct_pending_area.controls: admin_direct_pending_area.controls.append(ft.Text("တောင်းဆိုချက်မရှိပါ", size=11, color="grey"))

        # Direct Requests History
        req_h_res = supabase.table("requests").select("*, tutors(name)").neq("status", "pending").execute()
        for row in req_h_res.data:
            s_n = row.get("student_name"); s_p = row.get("student_phone"); r_rej = row.get("reject_reason"); r_stat = row.get("status")
            t_info = row.get("tutors") or {}
            t_n = t_info.get("name")
            if r_stat == 'completed':
                admin_direct_completed_area.controls.append(ft.Text(f"• [Success] ကျောင်းသား: {s_n} ({s_p}) -> ဆရာ: {t_n}", size=11, color="green", weight="bold"))
            else:
                admin_direct_completed_area.controls.append(ft.Text(f"• [Rejected] ကျောင်းသား: {s_n} -> ဆရာ: {t_n}\n  (Reason: {r_rej})", size=11, color="red"))
        if not admin_direct_completed_area.controls: admin_direct_completed_area.controls.append(ft.Text("ပြီးမြောက်မှုမရှိပါ", size=11, color="grey"))

        # Job Posts
        p_res = supabase.table("job_posts").select("*").eq("status", "pending").execute()
        for row in p_res.data:
            j_id = row.get("id"); s_name = row.get("stu_name"); s_phone = row.get("stu_phone"); subj = row.get("subject")
            j_state = row.get("state"); town = row.get("township"); fee = row.get("fee_offer")
            post_details = f"ကျောင်းသား: {s_name} (ဖုန်း: {s_phone})\nဒေသ: {j_state}, {town} | ဘာသာရပ်: {subj}\nနှုန်းထား: {fee} Ks"
            admin_posts_pending_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Text(post_details, size=12),
                ft.Row([
                    ft.Button(content=ft.Row([ft.Icon(ft.Icons.THUMB_UP, color="green"), ft.Text("တင်ခွင့်ပြု")], tight=True), on_click=lambda e, jid=j_id: [supabase.table("job_posts").update({"status": "approved"}).eq("id", jid).execute(), refresh_admin_view()]),
                    ft.Button(content=ft.Row([ft.Icon(ft.Icons.CLOSE, color="red"), ft.Text("Reject")], tight=True), on_click=lambda e, jid=j_id: [reject_target_id.__setitem__(0, jid), reject_target_type.__setitem__(0, "job_post"), setattr(reject_dialog, 'open', True), page.update()])
                ], spacing=10)
            ]))))
        if not admin_posts_pending_list.controls: admin_posts_pending_list.controls.append(ft.Text("စိစစ်ရန် Post မရှိသေးပါ။", size=12, color="grey"))
            
        p_app_res = supabase.table("job_posts").select("*").eq("status", "approved").execute()
        for row in p_app_res.data:
            j_id = row.get("id"); s_name = row.get("stu_name"); s_phone = row.get("stu_phone"); subj = row.get("subject")
            j_state = row.get("state"); town = row.get("township"); fee = row.get("fee_offer"); details = row.get("details")
            
            cnt_res = supabase.table("job_applications").select("id", count="exact").eq("job_id", j_id).execute()
            applicants_count = cnt_res.count if cnt_res.count is not None else len(cnt_res.data)
            
            admin_posts_approved_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Text(f"ကျောင်းသား/မိဘ: {s_name} (ဖုန်း: {s_phone})", size=12, weight="bold"),
                ft.Text(f"ဒေသ: {j_state}, {town} | လိုအပ်သောဘာသာရပ်: {subj}\nနှုန်းထား: {fee} Ks | အသေးစိတ်: {details}", size=12),
                ft.Divider(),
                ft.Row([
                    ft.TextButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PEOPLE, size=16, color="blue"),
                            ft.Text(f"လျှောက်ထားသူ ( {applicants_count} ) ယောက်", color="blue", weight="bold", size=11)
                        ], tight=True),
                        # --- [ဒီနေရာလေးကို sn နဲ့ sp အသစ်တိုးပြီး ပြင်ထားပါတယ်] ---
                        on_click=lambda e, jid=j_id, js=subj, sn=s_name, sp=s_phone: open_applicants_list_popup(jid, js, sn, sp) 
                    ),
                    ft.ElevatedButton(
                        "Done", icon=ft.Icons.CHECK_CIRCLE, bgcolor="green", color="white",
                        on_click=lambda e, jid=j_id: [supabase.table("job_posts").update({"status": "completed"}).eq("id", jid).execute(), refresh_admin_view()]
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
            ]))))
        if not admin_posts_approved_list.controls: admin_posts_approved_list.controls.append(ft.Text("အတည်ပြုထားသော Active Post မရှိသေးပါခင်ဗျာ။", size=11, color="grey"))
            
        p_comp_res = supabase.table("job_posts").select("*").eq("status", "completed").execute()
        for row in p_comp_res.data:
            s_name = row.get("stu_name"); s_phone = row.get("stu_phone"); subj = row.get("subject")
            j_state = row.get("state"); town = row.get("township"); fee = row.get("fee_offer"); details = row.get("details")
            admin_posts_completed_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                ft.Text(f"✅ ကျောင်းသား/မိဘ: {s_name} (ဖုန်း: {s_phone})", size=12, weight="bold", color="green"),
                ft.Text(f"ဒေသ: {j_state}, {town} | လိုအပ်သောဘာသာရပ်: {subj}\nနှုန်းထား: {fee} Ks | အသေးစိတ်: {details}", size=12),
                ft.Divider(),
                ft.Text("ဤ Post ကို ဆရာချိတ်ဆက်ပေးပြီး ဖြစ်ပါသည်။", color="grey", size=11, weight="bold")
            ]))))
        if not admin_posts_completed_list.controls: admin_posts_completed_list.controls.append(ft.Text("ချိတ်ဆက်ပြီးမြောက်သော Post မရှိသေးပါခင်ဗျာ။", size=11, color="grey"))

        page.update()

    admin_chat_layout = ft.Row([
        ft.Container(content=admin_chat_tutors_list, width=130, bgcolor="#F5F5F5", padding=5),
        ft.VerticalDivider(width=1), admin_chat_right_panel
    ], expand=True)

    admin_direct_layout = ft.Row([
        ft.Column([ft.Text("စိစစ်ဆဲတောင်းဆိုမှုများ", weight="bold", size=12, color="orange"), admin_direct_pending_area], expand=True),
        ft.VerticalDivider(width=1),
        ft.Column([ft.Text("ပြီးမြောက်ပြီးသမိုင်းကြောင်း", weight="bold", size=12, color="green"), admin_direct_completed_area], expand=True)
    ], expand=True)

    # =========================================================================
    # --- ADMIN DASHBOARD (Design အသစ်) ---
    # =========================================================================
    def create_admin_btn(icon, text, bgcolor, on_click_action):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=32, color="black"),
                ft.Text(text, color="black", weight="bold", size=13, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            width=145, height=130, bgcolor=bgcolor, border_radius=15, ink=True,
            on_click=on_click_action,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color="black12")
        )
    # --- ခလုတ်များနှင့် စာမျက်နှာများကို ချိတ်ဆက်ပေးသော Dictionary ---
    admin_panels_dict = {
        "new": admin_pending_list, 
        "approved_list": admin_approved_list, 
        "direct": admin_direct_layout, 
        "post_pending": admin_posts_pending_list,
        "post_approved": admin_posts_approved_list,
        "post_completed": admin_posts_completed_list, 
        "chat": admin_chat_layout, 
        "noti": admin_notification_list
    }

    admin_dashboard_view = ft.Column([
        ft.Row([
            create_admin_btn(ft.Icons.PERSON_ADD, "ဆရာသစ်\nအတည်ပြုရန်", "#B2DFDB", lambda _: show_admin_panel("new", "ဆရာသစ် အတည်ပြုရန်")),
            create_admin_btn(ft.Icons.ASSIGNMENT_IND, "ဆရာများ\nစာရင်း", "#B2DFDB", lambda _: show_admin_panel("approved_list", "ဆရာများ စာရင်း"))
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Row([
            create_admin_btn(ft.Icons.FIND_IN_PAGE, "စိစစ်ရန်\npost များ", "#BBDEFB", lambda _: show_admin_panel("post_pending", "စိစစ်ရန် Post များ")),
            create_admin_btn(ft.Icons.FACT_CHECK, "စိစစ်ပြီး\npost များ", "#BBDEFB", lambda _: show_admin_panel("post_approved", "စိစစ်ပြီး Post များ"))
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Row([
            create_admin_btn(ft.Icons.SWAP_HORIZ, "ချိတ်ဆက်ပြီး\nPost များ", "#D1C4E9", lambda _: show_admin_panel("post_completed", "ချိတ်ဆက်ပြီး Post များ")),
            create_admin_btn(ft.Icons.HANDSHAKE, "ဆရာများအား\nချိတ်ဆက်ခြင်း\nအတည်ပြုရန်", "#D1C4E9", lambda _: show_admin_panel("direct", "ချိတ်ဆက်ခြင်း အတည်ပြုရန်"))
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Row([
            create_admin_btn(ft.Icons.NOTIFICATIONS, "အချက်ပေးစာ\nNotification", "#FFCCBC", lambda _: show_admin_panel("noti", "အချက်ပေးစာ Notification")),
            create_admin_btn(ft.Icons.CHAT, "Chat\nစာပို့ခြင်း", "#FFCCBC", lambda _: show_admin_panel("chat", "Chat စာပို့ခြင်း"))
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Container(height=10),
        ft.Text("Designed by Saw Yan Aung", size=10, color="grey")
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)

    admin_content_area = ft.Container(content=admin_dashboard_view, expand=True)
    
    admin_back_btn = ft.IconButton(ft.Icons.ARROW_BACK, icon_color="blue", visible=False, on_click=lambda _: show_admin_dashboard())
    admin_title = ft.Text("ADMIN", size=20, weight="bold", color="#1a1a4b")

    def show_admin_dashboard():
        admin_content_area.content = admin_dashboard_view
        admin_back_btn.visible = False
        admin_title.value = "ADMIN"
        refresh_admin_view()
        page.update()

    def show_admin_panel(panel_key, title):
        admin_content_area.content = admin_panels_dict[panel_key]
        admin_back_btn.visible = True
        admin_title.value = title
        if panel_key == "chat": refresh_admin_chat_view()
        elif panel_key == "noti": refresh_admin_notifications()
        else: refresh_admin_view()
        page.update()

    # =========================================================================
    # --- ADMIN LOGOUT FUNCTION ---
    # =========================================================================
    def logout_admin():
        page.is_admin_logged_in = False
        main_container.content = admin_login_tab
        admin_pass_input.value = ""          
        admin_pass_input.border_color = None 
        admin_login_msg.value = ""           
        page.update()

    admin_logout_btn = ft.IconButton(ft.Icons.LOGOUT, icon_color="red", on_click=lambda _: logout_admin(), tooltip="Logout ထွက်မည်")

    admin_tab = ft.Column([
        ft.Row([
            ft.Row([admin_back_btn, admin_title]), # Back Button နဲ့ Title ကို ဘယ်ဘက်မှာထားမယ်
            admin_logout_btn # Logout Button ကို ညာဘက်အစွန်မှာထားမယ်
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        admin_content_area
    ], expand=True)

    # =========================================================================
    # --- ADMIN LOGIN TAB (Error ပြတဲ့ စနစ် ထည့်သွင်းထားသည်) ---
    # =========================================================================
    admin_login_msg = ft.Text(color="red") # Error ပြရန် စာတမ်း

    def do_admin_login(e):
        if admin_pass_input.value == "G&b862013":
            page.is_admin_logged_in = True
            main_container.content = admin_tab
            refresh_admin_view()
            
            # Password မှန်သွားရင် အနီရောင်နဲ့ စာတွေကို ပြန်ဖျောက်မယ်
            admin_login_msg.value = ""
            admin_pass_input.border_color = None
            admin_pass_input.value = "" # လုံခြုံရေးအရ Password အကွက်ကို ရှင်းထုတ်မည်
        else:
            # Password မှားခဲ့ရင်
            admin_login_msg.value = "Admin Password မှားယွင်းနေပါသည်။"
            admin_pass_input.border_color = "red"
            
        page.update()

    admin_login_tab = ft.Column([
        ft.Text("Admin Login", size=20, weight="bold"), 
        admin_pass_input, 
        admin_login_msg, # Error Message အကွက် ထည့်သွင်းခြင်း
        ft.Button("Login ဝင်မည်", on_click=do_admin_login, width=150)
    ], spacing=15, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # =========================================================================
    # --- ၅။ TERMS, HELP, BLACKLIST, USERGUIDE TABS ---
    # =========================================================================
    terms_content = ft.Column([
        ft.Text("Terms & Conditions (စည်းမျဉ်းစည်းကမ်းများ)", size=18, weight="bold", color="blue"),
        ft.Divider(),
        ft.Text("၁။ ဤ Platform သည် ဆရာနှင့် ကျောင်းသား တိုက်ရိုက်ချိတ်ဆက်ပေးသော နေရာသာဖြစ်သည်။\n\n၂။ချိတ်ဆက်မှု ဝန်ဆောင်ခကို ဆရာများဘက်မှ ပေးရပါမည်။ \n\n၃။ချိတ်ဆက်မှု ဝန်ဆောင်ခကို ကျောင်းသားများဘက်မှ ပေးစရာမလိုပါ။\n\n၄။ချိတ်ဆက်မှု ဝန်ဆောင်ခမှာ ပထမလ၏ ၂၀%ကို ပေးချေရမှာဖြစ်ပါသည်။\n\n၅။ကျောင်းသားမိဘများအနေဖြင့် လစာအား  ပထမဦးဆုံးနေ့တွင် ဆရာအား တစ်လစာ ကြိုတင်ပေးချေ ရပါမည်။\n\n၆။ အချက်အလက်များကို မှန်ကန်စွာ ဖြည့်စွက်ရပါမည်။\n\n၇။ လိမ်လည်မှုများ၊ စည်းကမ်းဖောက်ဖျက်မှုများ တွေ့ရှိပါက Blacklist သွင်းခံရပါမည်။", size=13)
    ], expand=True)
    terms_tab = ft.Container(content=terms_content, expand=True)

    help_content = ft.Column([
        ft.Text("Help & Support (အကူအညီ)", size=18, weight="bold", color="green"),
        ft.Divider(),
        ft.Text("အဆင်မပြေမှုများနှင့် အကြံပြုလိုသည်များ ရှိပါက ဆက်သွယ်နိုင်ပါသည်။", size=13),
        ft.Row([
            ft.Icon(ft.Icons.EMAIL, color="blue"),
            ft.Text("Email us : teachermatching@gmail.com", weight="bold", size=14)
        ])
    ], expand=True)
    help_tab = ft.Container(content=help_content, expand=True)

    teacher_guide_content = ft.Column([
        ft.Text("Teacher User Guide (ဆရာများအတွက် အသုံးပြုပုံ)", size=18, weight="bold", color="teal"),
        ft.Divider(),
        ft.Text("၁။ အကောင့်သစ်ပြုလုပ်ရန် Register တွင် မိမိ Username နှင့် Password ဖြည့်ပါ ၊ ပြီးနောက် ထို Username & Password ဖြင့် Login ဝင်ပါ(ဥပမာ - KyawKyaw, Kk@12345)။", size=13),
        ft.Text("၂။ Login ဝင်ပြီးနောက် မိမိ ကိုယ်ရေးအချက်အလက်၊ ဓာတ်ပုံ၊ သင်ကြားနိုင်သော အတန်း/ဘာသာရပ်များကို 'Profile ပြင်ဆင်မည်' နှိပ်၍ ဖြည့်စွက်ပါ။", size=13),
        ft.Text("၃။ အချက်အလက်များ ဖြည့်ပြီးပါက Admin ထံ အတည်ပြုချက်စောင့်ပါ။ Admin Approve ပေးမှသာ ကျောင်းသားများ မြင်တွေ့ရပါမည်။", size=13),
        ft.Text("၄။ 'Post များ' Tab တွင် ကျောင်းသားများ တင်ထားသော ဆရာခေါ်စာများကို လေ့လာ၍ 'Apply' နှိပ်ပြီး လျှောက်ထားနိုင်ပါသည်။", size=13),
        ft.Text("၅။ Admin နှင့် တိုက်ရိုက် စကားပြောလိုပါက 'Admin Chat' ကို အသုံးပြုနိုင်ပါသည်။", size=13),
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    teacher_guide_tab = ft.Container(content=teacher_guide_content, expand=True)

    student_guide_content = ft.Column([
        ft.Text("Student User Guide (ကျောင်းသား/မိဘများအတွက်)", size=18, weight="bold", color="orange"),
        ft.Divider(),
        ft.Text("၁။ 'ပထမဦးစွာ Register တွင် အကောင့်ပြုလုပ်ပါ၊ ပြီးနောက် ထို Username & Password ဖြင့် Login ဝင်ပါ (ဥပမာ - Username: MaMa, Password: မိမိဖုန်းနံပါတ်)။", size=13),
        ft.Text("၂။ 'ဆရာရှာရန်' တွင် မိမိနေထိုင်ရာ တိုင်းနှင့် မြို့နယ် ရွေးချယ်/ရိုက်ထည့်ပြီး ကိုက်ညီသော ဆရာများ၏ Profile ကို ကြည့်ရှုနိုင်ပါသည်။", size=13),
        ft.Text("၃။ သဘောကျသော ဆရာတွေ့ပါက 'ဒီဆရာနဲ့ သင်မယ်' ကိုနှိပ်၍ Admin ထံ တောင်းဆိုနိုင်ပါသည်။", size=13),
        ft.Text("၄။ 'Post တင်ရန်' တွင် မိမိလိုချင်သော ဘာသာရပ်၊ သင်ကြားလိုသော ဒေသနှင့် ပေးနိုင်သည့် ကြေးနှုန်းထားများ ဖြည့်စွက်၍ Post တင်နိုင်ပါသည်။", size=13),
        ft.Text("၅။ 'မိမိ၏ Post များ' Tab တွင် မိမိတင်ထားသော Post ကို ဆရာမည်မျှ လျှောက်ထားသည်ကို ကြည့်ရှုနိုင်ပါသည်။", size=13),
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    student_guide_tab = ft.Container(content=student_guide_content, expand=True)

    blacklist_list = ft.ListView(expand=True, spacing=10)
    
    def refresh_blacklist_view():
        blacklist_list.controls.clear()
        res = supabase.table("tutors").select("name, phone, reject_reason").eq("status", "blacklisted").execute()
        if not res.data:
            blacklist_list.controls.append(ft.Text("Black List စာရင်း မရှိသေးပါ။", color="grey", size=12))
        else:
            for row in res.data:
                n = row.get("name"); p = row.get("phone"); r = row.get("reject_reason")
                blacklist_list.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                    ft.Text(f"အမည်: {n if n else 'Unknown'}", weight="bold", color="red"),
                    ft.Text(f"ဖုန်း: {p if p else '-'}"),
                    ft.Text(f"အကြောင်းရင်း: {r if r else '-'}", color="grey", size=11)
                ]))))
        page.update()

    blacklist_content = ft.Column([
        ft.Text("Black Listed (အမည်ပျက်စာရင်း)", size=18, weight="bold", color="red"),
        ft.Divider(),
        blacklist_list
    ], expand=True)
    blacklist_tab = ft.Container(content=blacklist_content, expand=True)

    # =========================================================================
    # --- ၆။ NAVIGATION LOGIC ---
    # =========================================================================
    main_container = ft.Container(content=teacher_tab, padding=15, expand=True)

    # =========================================================================
    # --- HOME SCREEN (ပင်မစာမျက်နှာ Design သစ်) ---
    # =========================================================================
    def create_home_btn(icon, text, bgcolor, on_click_action, w, h=90, t_color="black"):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=28, color=t_color),
                ft.Text(text, color=t_color, weight="bold", size=12)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=w, height=h, bgcolor=bgcolor, border_radius=15, ink=True,
            on_click=on_click_action,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color="black12")
        )

    home_top_row = ft.Row([
        create_home_btn(ft.Icons.SCHOOL, "Teacher", "#C5E1A5", lambda _: navigate_to(teacher_tab, "Teacher Panel"), 100),
        create_home_btn(ft.Icons.PERSON, "Student", "#EF9A9A", lambda _: navigate_to(student_tab, "Student Area"), 100),
        create_home_btn(ft.Icons.SETTINGS, "Admin", "#CE93D8", lambda _: navigate_to(admin_login_tab if not page.is_admin_logged_in else admin_tab, "Admin Panel"), 100),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

    home_mid_row = ft.Row([
        create_home_btn(ft.Icons.SHIELD, "Black List", "#9FA8DA", lambda _: navigate_to(blacklist_tab, "Black Listed"), 155, h=65),
        create_home_btn(ft.Icons.HELP_OUTLINE, "Help\nSupport & FAQ", "#90CAF9", lambda _: navigate_to(help_tab, "Help & Support"), 155, h=65),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

    home_term_btn = ft.Row([
        create_home_btn(ft.Icons.ASSIGNMENT, "Term & Condition", "#A5D6A7", lambda _: navigate_to(terms_tab, "Terms & Conditions"), 330, h=65)
    ], alignment=ft.MainAxisAlignment.CENTER)

    home_guide_row = ft.Row([
        create_home_btn(ft.Icons.MENU_BOOK, "Teacher\nUserGuide", "#90CAF9", lambda _: navigate_to(teacher_guide_tab, "Teacher Guide"), 155, h=70),
        create_home_btn(ft.Icons.MENU_BOOK, "Student\nUserGuide", "#FFCCBC", lambda _: navigate_to(student_guide_tab, "Student Guide"), 155, h=70),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

    home_update_btn = ft.Row([
        create_home_btn(ft.Icons.DOWNLOAD, "Update APP", "#00796B", open_update_dialog, 330, h=60, t_color="white")
    ], alignment=ft.MainAxisAlignment.CENTER)

    home_view = ft.Column([
        ft.Container(height=10),
        ft.Text("ပင်မစာမျက်နှာ", size=24, weight="bold", color="#1a1a4b"),
        ft.Text("Teacher Match ဆရာရှာဖွေရေး\nAgency မှ ကြိုဆိုပါတယ်", text_align=ft.TextAlign.CENTER, size=15),
        ft.Container(height=15),
        home_top_row,
        ft.Container(height=15),
        home_mid_row,
        ft.Container(height=15),
        ft.Divider(),
        home_term_btn,
        ft.Text("အသုံးမပြုမီ Term & Condition ကို\nအရင်ဖတ်ပေးပါ", text_align=ft.TextAlign.CENTER, size=12),
        ft.Container(height=15),
        home_guide_row,
        ft.Container(height=15),
        home_update_btn,
        ft.Container(height=10),
        ft.Text(f"V {CURRENT_VERSION}", size=11, color="grey", weight="bold"),
        ft.Text("Powered by Saw Yan Aung", size=9, color="grey")
    ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)

    # =========================================================================
    # --- APP STARTUP (Navigation လမ်းကြောင်းအသစ်) ---
    # =========================================================================
    main_container = ft.Container(content=home_view, padding=15, expand=True)
    update_appbar(True) 
    page.add(main_container)

ft.run(main)
