##########  运行前需要调用字体文件：simsun.ttc ##########
import threading
import time
import pygame
import sys
import pygame.font

# 参数配置
WINDOW_SIZE = 5     # 窗口大小
TIME_OUT = 8       # 超时时间（秒）
TOTAL_PACKETS = 16  # 总共要发送的数据包数量

# 颜色定义
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0) # 黄色，表示发送窗口中待发送的帧
GREEN = (0, 255, 0) # 绿色，表示该帧已经收到ACK
RED = (255, 0, 0) # 红色，表示该帧超时需要重传
BLUE = (0, 0, 255) # 蓝色，表示接收方已经收到的帧
BLACK = (0, 0, 0)
PURPLE = (160, 32, 240)  # 紫色，表示接收方期望的下一帧
GRAY = (200, 200, 200)

# 初始化 Pygame
pygame.init()
font = pygame.font.Font("simsun.ttc",20)
font1 = pygame.font.Font("simsun.ttc",30)
font2 = pygame.font.Font("simsun.ttc",15)
screen_width, screen_height = 1010, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('后退N帧ARQ算法模拟')
clock = pygame.time.Clock()

#定义log类
class Log:
    def __init__(self, x, y, width, height, font, title, max_lines=20):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.max_lines = max_lines
        self.title = title  
        self.lines = []
        self.lock = threading.Lock()
        self.scroll_offset = 0  # 当前滚动位置（第一行的索引）

        # 计算可见的最大行数
        self.line_height = self.font.get_height() + 2
        self.max_visible_lines = self.height // self.line_height

        # 滚动条参数
        self.scrollbar_width = 20
        self.scrollbar_rect = pygame.Rect(
            self.x + self.width - self.scrollbar_width, self.y, self.scrollbar_width, self.height
        )
        self.thumb_height = max(int(self.height * self.max_visible_lines / self.max_lines), 20)
        self.thumb_rect = pygame.Rect(
            self.scrollbar_rect.x, self.scrollbar_rect.y, self.scrollbar_width, self.thumb_height
        )
        self.is_dragging = False
        self.drag_offset = 0

    def add_message(self, message):
        with self.lock:
            self.lines.append(message)
            if self.scroll_offset <= len(self.lines) - self.max_visible_lines:
                self.scroll_offset = max(len(self.lines) - self.max_visible_lines, 0)
            self.update_thumb()

    def scroll_up(self):
        with self.lock:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
                self.update_thumb()

    def scroll_down(self):
        with self.lock:
            if self.scroll_offset < max(len(self.lines) - self.max_visible_lines, 0):
                self.scroll_offset += 1
                self.update_thumb()
    
    def update_thumb(self):
        if len(self.lines) <= self.max_visible_lines:
            self.thumb_rect.height = self.scrollbar_rect.height
            self.thumb_rect.y = self.scrollbar_rect.y
        else:
            self.thumb_rect.height = max(int(self.scrollbar_rect.height * self.max_visible_lines / len(self.lines)), 20)
            self.thumb_rect.y = self.scrollbar_rect.y + int(
                (self.scroll_offset / (len(self.lines) - self.max_visible_lines)) *
                (self.scrollbar_rect.height - self.thumb_rect.height)
            )
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                mouse_pos = event.pos
                if self.thumb_rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self.drag_offset = mouse_pos[1] - self.thumb_rect.y
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_y = event.pos[1]
                new_thumb_y = mouse_y - self.drag_offset

                # 限制 thumb 的位置在滚动条范围内
                new_thumb_y = max(self.scrollbar_rect.y, min(new_thumb_y, self.scrollbar_rect.y + self.scrollbar_rect.height - self.thumb_rect.height))
                self.thumb_rect.y = new_thumb_y

                # 计算 scroll_offset
                if self.scrollbar_rect.height - self.thumb_rect.height > 0:
                    scroll_ratio = (self.thumb_rect.y - self.scrollbar_rect.y) / (self.scrollbar_rect.height - self.thumb_rect.height)
                    self.scroll_offset = int(scroll_ratio * (len(self.lines) - self.max_visible_lines))
                    self.scroll_offset = max(min(self.scroll_offset, len(self.lines) - self.max_visible_lines), 0)

    def draw(self, screen):
        # 绘制背景
        pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height))
        # 绘制边框
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        # 绘制标题
        title_surface = self.font.render(self.title, True, BLACK)
        screen.blit(title_surface, (self.x + 5, self.y - 30))
        # 绘制每一行日志
        with self.lock:
            start = self.scroll_offset
            end = min(self.scroll_offset + self.max_visible_lines, len(self.lines))
            for idx, line in enumerate(self.lines[start:end]):
                text_surface = self.font.render(line, True, BLACK)
                screen.blit(text_surface, (self.x + 5, self.y + 5 + idx * self.line_height))
        # 绘制滚动条轨道
        pygame.draw.rect(screen, (180, 180, 180), self.scrollbar_rect)
        # 绘制滚动条滑块
        pygame.draw.rect(screen, (100, 100, 100), self.thumb_rect)

#log窗口初始化
log_width =( screen_width - 20 )// 2 # 宽度
log_height = 200
log_x = 10  # 左边距
log_y = 400  # 上边距
log = Log(log_x, log_y, log_width, log_height - 20, font, title="系统日志", max_lines=15)

# 数据帧类
class Frame:
    def __init__(self, seq, x, y, dest_y, ack=False):
        self.seq = seq
        self.x = x
        self.y = y
        self.dest_y = dest_y
        self.speed = 1
        self.color = YELLOW
        self.ack = ack
        self.active = True

        if self.ack:
            self.color = GREEN  # ACK 帧颜色为绿色

    def move(self):
        if self.y < self.dest_y:
            self.y += self.speed
            if self.y >= self.dest_y:
                self.y = self.dest_y
                self.active = False
        elif self.y > self.dest_y:
            self.y -= self.speed
            if self.y <= self.dest_y:
                self.y = self.dest_y
                self.active = False

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x - 10, self.y, 40, 20))
        seq_text = font.render(str(self.seq), True, BLACK)
        screen.blit(
            seq_text, 
            (self.x +10 - seq_text.get_width() // 2, self.y + 10 - seq_text.get_height() // 2)
        )
    def is_clicked(self, pos):#规定鼠标点到范围内
        rect = pygame.Rect(self.x - 10, self.y, 40, 20)
        return rect.collidepoint(pos)

class Sender:
    def __init__(self):
        self.base = 0                    # 窗口起始序号
        self.next_seq = 0                # 下一个待发送的序号
        self.lock = threading.Lock()
        self.timers = {}                 # 序号对应的计时器
        self.packets_status = ['white'] * TOTAL_PACKETS
        self.frames = []
        self.fnode = None
        self.running = True
        self.finished = False            # 完成标志

    def send_packets(self):
        while self.base < TOTAL_PACKETS and self.running:
            self.lock.acquire()
            # 计算当前在发送窗口内的未确认帧数量
            in_flight = self.next_seq - self.base
            if in_flight < WINDOW_SIZE and self.next_seq < TOTAL_PACKETS:
                self.send_packet(self.next_seq)
                self.next_seq += 1
                self.lock.release()
                time.sleep(0.5)  # 每发送一个帧后暂停0.5秒
            else:
                self.lock.release()
                time.sleep(0.1)  # 窗口已满，等待ACK

            # 检查是否所有数据包都已确认
            self.lock.acquire()
            if self.base >= TOTAL_PACKETS:
                if all(status == 'green' for status in self.packets_status):
                    self.finished = True
                    self.lock.release()
                    break
            self.lock.release()

    def send_packet(self, seq):
        print(f"发送方:发送数据包 {seq}")
        log.add_message(f"发送方:发送数据包 {seq}")
        self.update_packet_status(seq, 'yellow')
        frame = Frame(seq, 70 + seq * 60, 130, 250)
        self.frames.append(frame)
        self.start_timer(seq)

    def start_timer(self, seq):
        timer = threading.Timer(TIME_OUT, self.timeout, args=(seq,))
        timer.start()
        self.timers[seq] = timer

    def timeout(self, seq):
        self.lock.acquire()
        print(f"发送方:数据包 {seq} 超时，重传窗口从数据包 {self.base} 开始")
        log.add_message(f"发送方:数据包 {seq} 超时，重传窗口从数据包 {self.base} 开始")
        # 停止所有计时器
        for t in self.timers.values():
            t.cancel()
        self.timers.clear()
        # 重发窗口内的所有数据包
        self.next_seq = self.base
        for i in range(self.base, self.base + WINDOW_SIZE):
            if i < TOTAL_PACKETS:
                self.update_packet_status(i, 'red')
        self.lock.release()

    def receive_ack(self, ack):
        self.lock.acquire()
        # 创建 ACK 帧
        ack_frame = Frame(ack + 1, 70 + ack * 60, 250, 130, ack=True)
        self.frames.append(ack_frame)
        self.lock.release()

    def update_packet_status(self, seq, color):
        self.packets_status[seq] = color

    def stop(self):
        self.running = False
        # 取消所有计时器
        self.lock.acquire()
        for t in self.timers.values():
            t.cancel()
        self.timers.clear()
        self.lock.release()

class Receiver:
    def __init__(self):
        self.expected_seq = 0
        self.packets_status = ['white'] * TOTAL_PACKETS
        self.sender = None
        self.running = True

    def set_sender(self, sender):
        self.sender = sender

    def receive_packets(self):
        while self.expected_seq < TOTAL_PACKETS and self.running:
            time.sleep(0.1)  # 每隔0.1秒检查一次

    def check_frame(self, frame):
        if frame.y == frame.dest_y and not frame.ack and frame.active == False:###
            print(f"接收方:收到数据包 {frame.seq}")
            log.add_message(f"接收方:收到数据包 {frame.seq}")
            if frame.seq == self.expected_seq:
                self.update_packet_status(frame.seq, 'blue')
                # 发送 ACK
                print(f"接收方:发送 ACK {frame.seq}")
                log.add_message(f"接收方:发送 ACK {frame.seq}")
                self.sender.receive_ack(frame.seq)
                self.expected_seq += 1
            else:
                print(f"接收方:收到的序列号 {frame.seq} 不符合预期 {self.expected_seq}")
                log.add_message(f"接收方:收到的序列号 {frame.seq} 不符合预期 {self.expected_seq}")
                # 在 Go-Back-N 中，如果收到不期望的帧，会发送最后一个已确认的 ACK
                if self.expected_seq > 0:
                    last_ack = self.expected_seq - 1
                    print(f"发送 ACK {last_ack}")
                    log.add_message(f"发送 ACK {last_ack}")
                    self.sender.receive_ack(last_ack)
            return True
        elif frame.y == frame.dest_y and frame.ack and frame.active == False:
            print(f"发送方:已收到ACK 帧 {frame.seq}")
            log.add_message(f"发送方:已收到ACK 帧 {frame.seq}")
            return True
        return False

    def update_packet_status(self, seq, color):
        self.packets_status[seq] = color

    def stop(self):
        self.running = False

def draw_window(sender, receiver):
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sender.stop()
            receiver.stop()
            pygame.quit()
            sys.exit()
    # 绘制发送方窗口
    pygame.draw.rect(screen, BLACK, (5, 50, 1000, 60), 2)
    sender_text = font1.render('发送方', True, BLACK)
    screen.blit(sender_text, (10, 20))
    for i in range(TOTAL_PACKETS):
        color_name = sender.packets_status[i]
        color = get_color(color_name)
        pygame.draw.rect(screen, color, (50 + i * 60, 60, 50, 40))
        seq_text = font.render(str(i), True, BLACK)
        screen.blit(seq_text, 
                    (75 + i * 60 - seq_text.get_width() // 2, 
                     80 - seq_text.get_height() // 2))

    # 绘制接收方窗口
    pygame.draw.rect(screen, BLACK, (5, 280, 1000, 60), 2)
    receiver_text = font1.render('接收方', True, BLACK)
    screen.blit(receiver_text, (10, 250))
    for i in range(TOTAL_PACKETS):
        if i == receiver.expected_seq:
            color = PURPLE  # 用紫色表示期望的下一帧
        else:
            color_name = receiver.packets_status[i]
            color = get_color(color_name)
        pygame.draw.rect(screen, color, (50 + i * 60, 290, 50, 40))
        seq_text = font.render(str(i), True, BLACK)
        screen.blit(seq_text, 
                    (75 + i * 60 - seq_text.get_width() // 2, 
                     310 - seq_text.get_height() // 2))

    for frame in sender.frames:
        frame.move()
        frame.draw()    
    #绘制log窗口
    log.draw(screen)
    #绘制文字解释窗口
    pygame.draw.rect(screen, "lightblue", ((screen_width - 20)// 2 + 20, 400, (screen_width - 10)// 2 - 20, 180), 2)
    explain_text = font2.render('发送窗口大小为5', True, BLACK)
    explain_text1 = font2.render('时钟超时时间为8秒', True, BLACK)
    explain_text2 = font2.render('黄色代表发送窗口中的帧已发送', True, BLACK)
    explain_text3 = font2.render('蓝色代表接收方已收到的帧', True, BLACK)
    explain_text4 = font2.render('红色代表接收超时需要重新发送数据帧', True, BLACK)
    explain_text5 = font2.render('绿色代表发送方已经收到相应ACK',True, BLACK)
    explain_text6 = font2.render('紫色代表接收方期待收到的帧',True, BLACK)
    screen.blit(explain_text, ((screen_width - 20)// 2 + 25, 405))
    screen.blit(explain_text1, ((screen_width - 20)// 2 + 25, 425))
    screen.blit(explain_text2, ((screen_width - 20)// 2 + 25, 445))
    screen.blit(explain_text3, ((screen_width - 20)// 2 + 25, 465))
    screen.blit(explain_text4, ((screen_width - 20)// 2 + 25, 485))
    screen.blit(explain_text5, ((screen_width - 20)// 2 + 25, 505))
    screen.blit(explain_text6, ((screen_width - 20)// 2 + 25, 525))
    pygame.display.update()

def get_color(color_name):
    if color_name == 'white':
        return WHITE
    elif color_name == 'yellow':
        return YELLOW
    elif color_name == 'green':
        return GREEN
    elif color_name == 'red':
        return RED
    elif color_name == 'blue':
        return BLUE
    elif color_name == 'purple':
        return PURPLE
    else:
        return GRAY

def main():
    sender = Sender()
    receiver = Receiver()
    receiver.set_sender(sender)

    sender_thread = threading.Thread(target=sender.send_packets)
    receiver_thread = threading.Thread(target=receiver.receive_packets)

    sender_thread.start()
    receiver_thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_ESCAPE]:
                sender.stop()
                receiver.stop()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEMOTION:
                # 传递事件给日志类以处理滚动条
                log.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:  # 鼠标滚轮上滚
                        log.scroll_up()
                    elif event.button == 5:  # 鼠标滚轮下滚
                        log.scroll_down()
                    elif event.button == 1:  # 鼠标左键点击
                        mouse_pos = pygame.mouse.get_pos()
                        sender.lock.acquire()
                        for frame in sender.frames:
                            if frame.active and frame.is_clicked(mouse_pos):
                                print(f"帧 {frame.seq} 被点击，标记为丢失或者损坏")
                                frame.active = True
                                sender.frames.remove(frame)
                                break  # 一次只处理一个帧
                        sender.lock.release()

        # 移动所有帧
        for frame in sender.frames:
            frame.move()

        # 检查帧状态
        to_remove = []
        for frame in sender.frames:
            if frame.active:
                continue
            if frame.ack:
                ack = frame.seq
                print(f"发送方:已收到ACK {ack}")
                log.add_message(f"发送方:已收到ACK {ack}")
                # 更新所有小于 ack 的数据包为绿色
                sender.lock.acquire()
                for seq in range(sender.base, ack):
                    if seq < TOTAL_PACKETS and sender.packets_status[seq] != 'green':
                        sender.update_packet_status(seq, 'green')
                        if seq in sender.timers:
                            sender.timers[seq].cancel()
                            del sender.timers[seq]
                sender.base = ack
                sender.lock.release()
                to_remove.append(frame)
            else:
                if receiver.check_frame(frame):
                    to_remove.append(frame)
        for frame in to_remove:
            sender.frames.remove(frame)

        # 绘制窗口和帧
        draw_window(sender, receiver)
        
        clock.tick(30)  # 控制帧率

if __name__ == "__main__":
    main()