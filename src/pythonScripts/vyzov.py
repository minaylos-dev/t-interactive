import time
from trackball_lib import Trackball

ball = Trackball()
ball.start()

while True:
    print(f"rx={ball.rx:+7.2f}  ry={ball.ry:+7.2f}  rz={ball.rz:+7.2f}  "
          f"||  wx={ball.wx:+7.2f}  wy={ball.wy:+7.2f}  wz={ball.wz:+7.2f}")
    time.sleep(0.1)