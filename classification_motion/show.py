import serial
import re
import pygame
import time
import threading

# Các biến toàn cục để chia sẻ dữ liệu giữa các luồng
current_status = "Unknown"
should_exit = False
oldstate = ""
def read_from_serial(port, baud_rate=115200, threshold=0.9):
    """
    Đọc dữ liệu từ cổng serial và cập nhật trạng thái hiện tại
    
    Args:
        port (str): Cổng serial (ví dụ: 'COM3' trên Windows, '/dev/ttyUSB0' trên Linux)
        baud_rate (int): Tốc độ baudrate
        threshold (float): Ngưỡng giá trị (mặc định là 0.9 tương đương 90%)
    """
    global current_status, should_exit
    
    try:
        # Thiết lập kết nối serial
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"Đã kết nối đến {port} với baudrate {baud_rate}")
        
        while not should_exit:
            # Đọc dữ liệu từ serial
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                print(f"Dữ liệu nhận được: {line}")
                
                # Phân tích dữ liệu
                high_values = parse_string_for_high_values(line, threshold)
                
                if high_values:
                    # Cập nhật trạng thái hiện tại (chọn trạng thái đầu tiên nếu có nhiều)
                    current_status = list(high_values.keys())[0]
                    print(f"Trạng thái hiện tại: {current_status}")
            
            # Ngủ một chút để không chiếm quá nhiều CPU
            time.sleep(0.1)
    
    except serial.SerialException as e:
        print(f"Lỗi kết nối serial: {e}")
        current_status = "Error"
    finally:
        # Đảm bảo đóng kết nối khi hoàn thành
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Đã đóng kết nối serial")

def parse_string_for_high_values(data_string, threshold=0.9):
    """
    Phân tích chuỗi dữ liệu để tìm các giá trị lớn hơn ngưỡng
    
    Args:
        data_string (str): Chuỗi dữ liệu từ serial
        threshold (float): Ngưỡng giá trị (mặc định là 0.9 tương đương 90%)
        
    Returns:
        dict: Từ điển chứa các trạng thái có giá trị cao hơn ngưỡng
    """
    # Sử dụng regex để tìm các mẫu "key: value"
    pattern = r'(\w+):\s+(\d+\.\d+)'
    matches = re.findall(pattern, data_string)
    
    # Tạo từ điển từ các kết quả và lọc các giá trị cao
    high_values = {}
    for key, value in matches:
        float_value = float(value)
        if float_value > threshold:
            high_values[key] = float_value
    
    return high_values

def display_status_window():
    """
    Hiển thị cửa sổ trạng thái sử dụng Pygame
    """
    global current_status, should_exit
    
    # Khởi tạo Pygame
    pygame.init()
    
    # Thiết lập cửa sổ
    width, height = 600, 400
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Serial Status Display")
    
    # Thiết lập font
    font_large = pygame.font.SysFont('Arial', 64)
    font_small = pygame.font.SysFont('Arial', 32)
    
    # Định nghĩa màu sắc
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    
    # Dictionary chứa màu cho từng trạng thái
    status_colors = {
        "idle": GREEN,
        "up_down": BLUE,
        "left_right": RED,
        "circle": YELLOW,
        "None": WHITE,
        "Unknown": WHITE,
        "Error": (255, 0, 0)
    }
    
    clock = pygame.time.Clock()
    
    # Vòng lặp chính
    running = True
    while running and not should_exit:
        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                should_exit = True
        
        # Xóa màn hình
        screen.fill(BLACK)
        
        # Hiển thị trạng thái hiện tại
        status_text = font_large.render(current_status, True, status_colors.get(current_status, WHITE))
        status_rect = status_text.get_rect(center=(width//2, height//2 - 50))
        screen.blit(status_text, status_rect)
        
        # Hiển thị hướng dẫn
        instruction_text = font_small.render("Press ESC to exit", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(width//2, height - 50))
        screen.blit(instruction_text, instruction_rect)
        
        # Cập nhật màn hình
        pygame.display.flip()
        
        # Kiểm tra phím ESC để thoát
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False
            should_exit = True
        
        # Giới hạn FPS
        clock.tick(30)
    
    # Kết thúc Pygame
    pygame.quit()

def simulate_serial_data():
    """
    Mô phỏng dữ liệu serial cho mục đích thử nghiệm
    """
    global current_status, should_exit
    
    sample_data = [
        "circle: 0.000000\nidle: 0.996094\nleft_right: 0.000000\nup_down: 0.000000",
        "circle: 0.000000\nidle: 0.100000\nleft_right: 0.950000\nup_down: 0.000000",
        "circle: 0.000000\nidle: 0.000000\nleft_right: 0.000000\nup_down: 0.980000",
        "circle: 0.950000\nidle: 0.000000\nleft_right: 0.000000\nup_down: 0.000000"
    ]
    
    index = 0
    while not should_exit:
        # Đọc dữ liệu mẫu theo vòng lặp
        data = sample_data[index]
        print(f"Dữ liệu mô phỏng: {data}")
        
        # Phân tích dữ liệu
        high_values = parse_string_for_high_values(data, 0.9)
        
        if high_values:
            # Cập nhật trạng thái hiện tại
            current_status = list(high_values.keys())[0]
            print(f"Trạng thái hiện tại: {current_status}")
        else:
            current_status = "None"
        
        # Chuyển đến mẫu tiếp theo
        index = (index + 1) % len(sample_data)
        
        # Chờ một khoảng thời gian trước khi cập nhật
        time.sleep(2)

def main():
    """
    Hàm chính để chạy ứng dụng
    
    Args:
        use_real_serial (bool): Nếu True, sử dụng kết nối serial thực tế. Nếu False, mô phỏng dữ liệu.
    """
    global should_exit
    
    # Tạo luồng hiển thị
    display_thread = threading.Thread(target=display_status_window)
    display_thread.start()
    
    # Tạo luồng đọc dữ liệu

    # Sử dụng kết nối serial thực tế
    PORT = 'COM3'  # Thay đổi thành cổng phù hợp với hệ thống của bạn
    serial_thread = threading.Thread(target=read_from_serial, args=(PORT,))

    
    serial_thread.start()
    
    try:
        # Chờ các luồng kết thúc
        display_thread.join()
        serial_thread.join()
    except KeyboardInterrupt:
        print("Chương trình bị ngắt bởi người dùng")
        should_exit = True
    
    print("Chương trình kết thúc")

if __name__ == "__main__":
    # Đặt use_real_serial=True để sử dụng kết nối serial thực
    # Đặt use_real_serial=False để mô phỏng dữ liệu cho mục đích thử nghiệm
    main()