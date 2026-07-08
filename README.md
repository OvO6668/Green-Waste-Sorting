Introduction

This project addresses the "last 100 meters" problem of waste sorting in residential communities. Residents often misclassify waste, manual supervision is costly, and hazardous waste mixed with general waste poses safety risks. We designed a desktop smart waste sorting prototype that automatically identifies and sorts four categories of waste, reducing community pollution and potential hazards.

The device adopts a "master-slave control" architecture: the host uses an RDK X5 development board for image recognition and decision-making, while the slave uses an ESP32 controller to drive the robotic arm for sorting. Structural components are designed in SolidWorks and 3D-printed, with modular assembly, hidden wiring, and enclosed mainboards for easy maintenance and iteration.

Features

Four-category sorting: Recyclables, Kitchen waste, Hazardous waste, Other waste
Visual recognition: Based on lightweight YOLOv11 model, recognizes several common waste types
Orange, Green apple, Medicine box, Transparent pill blister pack, Cosmetic empty bottle, Disposable cup, Sponge
Automatic sorting: Robotic arm precisely grabs waste and drops into corresponding bins
Offline operation: No internet or computer required, plug-and-play

Hardware

| Component | Model/Spec |
|-----------|-----------|
| Host | RDK X5 (Sunrise X3 chip, 10 TOPS) |
| Camera | 8MP AF Auto-focus USB2.0 IMX179 |
| Controller | ESP32 |
| Robotic Arm | Medium arm (35kg.cm + 20kg.cm servos, max 500g payload) |
| Structure | SolidWorks + 3D Printing |

Workflow

1.Power on & Self-check: RDK X5 initializes, arm returns to origin
2.Capture & Recognize: Camera captures image, YOLOv11 extracts features and classifies
3.Error Handling: Retry if not recognized within 3 seconds, fallback to "Other waste" after consecutive failures
4.Robotic Sorting: Commands sent via UART, arm moves, grabs, and precisely drops into correct bin
5.Reset & Wait: Arm returns to origin, awaiting next disposal

Tech Stack

Edge Computing: RDK X5 + Sunrise X3 chip
Object Detection: YOLOv11 lightweight model
Motion Control: ESP32 + UART communication
Mechanical Design: SolidWorks + 3D Printing
Languages: Arduino C++ (basic syntax, servo control, serial communication), Python (basic syntax, OpenCV image processing, serial communication)

Installation

bash
# Clone repository
git clone https://github.com/OvO6668/Green-Waste-Sorting.git
cd Green-Waste-Sorting
Demo Video
 
Bilibili Demo Video (<iframe src="//player.bilibili.com/player.html?isOutside=true&aid=116885773357487&bvid=BV1xjM56TEwq&cid=39772293678&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>)
License
This project is licensed under the MIT License.
Team
 
Project Name: Smart Waste Sorting Machine
 
Advisor: Zou Li
 
Team Leader: Huang Jiayi
 
Team Members: He Libing, Cheng Zhibin
 
Institution: Xiamen Huaxia University, School of Information & Intelligent Mechatronics
 
Major: 2025 Robotics Engineering
 
Category: Undergraduate Creative Group
Acknowledgments
Thanks to D-Robotics for providing the RDK X5 development board and technical support.
