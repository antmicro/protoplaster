if [ "$(command -v ifconfig)" ]
then
    ifconfig
else
    ip a
fi