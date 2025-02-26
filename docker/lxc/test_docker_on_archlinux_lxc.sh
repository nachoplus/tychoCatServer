# FROM: https://memcpy.io/running-docker-privileged-inside-of-lxc-lxd.html
lxc launch images:archlinux/current archlinux-catserver
lxc launch images:ubuntu/bionic archlinux-catserver

lxc config set archlinux-catserver security.nesting true
lxc config set archlinux-catserver security.privileged true
cat <<EOT | lxc config set archlinux-catserver raw.lxc -
lxc.cgroup.devices.allow = a
lxc.cap.drop =
EOT

lxc restart archlinux-catserver

cat <<EOT | lxc exec archlinux-catserver bash -
pacman -S --noconfirm docker docker-compose git
systemctl start docker
docker run --privileged hello-world
git clone https://github.com/nachoplus/tychoCatServer.git
cd tychoCatServer/docker
docker-compose up --build
EOT
