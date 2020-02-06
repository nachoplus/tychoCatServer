# FROM: https://memcpy.io/running-docker-privileged-inside-of-lxc-lxd.html
lxc launch images:ubuntu/bionic container

lxc config set container security.nesting true
lxc config set container security.privileged true
cat <<EOT | lxc config set container raw.lxc -
lxc.cgroup.devices.allow = a
lxc.cap.drop =
EOT

lxc restart container

cat <<EOT | lxc exec container bash -
apt install  -y docker.io docker-compose git
docker run --privileged hello-world
git clone https://github.com/nachoplus/tychoCatServer.git
cd tychoCatServer/docker
docker-compose up --build
EOT
