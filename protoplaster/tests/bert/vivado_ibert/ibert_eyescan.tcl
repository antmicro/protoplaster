proc perform_eye_scan { outputPath hwServer serialNumber channelPath prbsBits loopback } {
	# Connect to the emulator
	open_hw_manager
	connect_hw_server -url "$hwServer"
	open_hw_target "$hwServer/xilinx_tcf/Xilinx/$serialNumber"
	# Program and Refresh the device
	current_hw_device [lindex [get_hw_devices] 0]
	refresh_hw_device -update_hw_probes false [lindex [get_hw_devices] 0]
	set fullPath "$hwServer/xilinx_tcf/Xilinx/$serialNumber/$channelPath"
	set xil_newLinks [list]
	set xil_newLink [create_hw_sio_link -description {Link 0} [lindex [get_hw_sio_txs $fullPath/TX] 0] [lindex [get_hw_sio_rxs $fullPath/RX] 0] ]
	lappend xil_newLinks $xil_newLink
	set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
	unset xil_newLinks
	if { $loopback } {
		# Set link to use PCS Loopback, and write to hardware
		set_property LOOPBACK {Far-End PCS} [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
	}
	set_property RX_PATTERN "PRBS $prbsBits-bit" [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
	set_property TX_PATTERN "PRBS $prbsBits-bit" [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
	commit_hw_sio [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
	# Create, run, and save scan
	set xil_newScan [create_hw_sio_scan -description {Scan 0} 2d_full_eye  [lindex [get_hw_sio_links $fullPath/TX->$fullPath/RX] 0 ]]
	run_hw_sio_scan [get_hw_sio_scans $xil_newScan]
	wait_on_hw_sio_scan [get_hw_sio_scans $xil_newScan]
	write_hw_sio_scan -force $outputPath [get_hw_sio_scans $xil_newScan]
}

set requiredArgs 6
if { $argc != $requiredArgs } {
	puts "Incorrect argument count, got $argc, expected $requiredArgs"
	exit 1
}

set outputPath [lindex $argv 0]
set hwServer [lindex $argv 1]
set serialNumber [lindex $argv 2]
set channelPath [lindex $argv 3]
set prbsBits [lindex $argv 4]
set loopback [lindex $argv 5]

perform_eye_scan $outputPath $hwServer $serialNumber $channelPath $prbsBits $loopback
