import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def parse_transaction(text: str) -> dict:
    """
    Sử dụng Gemini API để phân tích tin nhắn người dùng thành JSON.
    Trả về dict nếu thành công, None nếu có lỗi hoặc không thể phân tích.
    """
    if not GEMINI_API_KEY:
        return None

    prompt = f"""
    Bạn là trợ lý tài chính doanh nghiệp. Hãy phân tích tin nhắn giao dịch sau đây của người dùng và trả về một đối tượng JSON duy nhất (không có markdown formatting, không có text dư thừa, chỉ đúng JSON).
    
    Quy tắc phân tích:
    1. "action": Một trong ["expense", "income", "transfer"]. Mặc định là "expense" trừ khi người dùng nói rõ là nhận tiền, có doanh thu (income) hoặc chuyển tiền (transfer).
    2. "amount": Số tiền (kiểu số nguyên). Ví dụ: "50k" -> 50000, "2 triệu" -> 2000000, "1.5tr" -> 1500000.
    3. "category": Danh mục chi/thu (tiếng Anh ngắn gọn, chọn từ danh sách: "salary", "office", "marketing", "operations", "equipment", "inventory", "rent", "utilities", "taxes", "entertainment", "production", "sales", "other").
    4. "bank": Tên ngân hàng/ví (VD: "VCB", "ACB", "CASH", "MOMO", v.v.). Nếu người dùng không nhắc đến, trả về null.
    5. "from_bank" & "to_bank": Chỉ dùng cho action="transfer". Tên tài khoản gửi đi và tài khoản nhận. Nếu không nhắc đến, trả về null.
    6. "description": Tóm tắt nội dung giao dịch thật ngắn gọn.
    
    Ví dụ 1: "trả tiền điện nước tháng này 5 triệu từ vcb"
    -> {{"action": "expense", "amount": 5000000, "category": "utilities", "bank": "VCB", "description": "tiền điện nước"}}
    
    Ví dụ 2: "chuyển 20 triệu từ acb sang tiền mặt để nhập hàng"
    -> {{"action": "transfer", "amount": 20000000, "from_bank": "ACB", "to_bank": "CASH", "description": "nhập hàng"}}
    
    Ví dụ 3: "nhận doanh thu dự án 150tr vào VCB"
    -> {{"action": "income", "amount": 150000000, "category": "sales", "bank": "VCB", "description": "doanh thu dự án"}}
    
    Ví dụ 4: "mua giấy in vpp 250k"
    -> {{"action": "expense", "amount": 250000, "category": "office", "bank": null, "description": "mua giấy in vpp"}}
    
    Tin nhắn của người dùng: "{text}"
    JSON output:
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        # Bóc tách JSON từ response
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:-3]
        elif result_text.startswith("```"):
            result_text = result_text[3:-3]
            
        data = json.loads(result_text.strip())
        return data
    except Exception as e:
        print(f"Lỗi Gemini API: {e}")
        return None
