proc perform_eye_scan { outputPath hwServer serialNumber channelPath prbsBits loopback reportFile dwellMode dwellValue } {
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

	set link_obj [lindex [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]] 0]
	set line_rate [get_property LINE_RATE $link_obj]
	set status [get_property STATUS $link_obj]

	set fid [open $reportFile "w"]
	puts $fid "LINE_RATE=$line_rate"
	puts $fid "TRANSCEIVER_STATUS=$status"
	close $fid

	# Create, run, and save scan
	set xil_newScan [create_hw_sio_scan -description {Scan 0} 2d_full_eye  [lindex [get_hw_sio_links $fullPath/TX->$fullPath/RX] 0 ]]

	if { $dwellMode eq "BER" } {
		if { $dwellValue ne "" } {
			set_property DWELL_BER $dwellValue [get_hw_sio_scans $xil_newScan]
		}
	} elseif { $dwellMode eq "TIME" } {
		set_property DWELL TIME [get_hw_sio_scans $xil_newScan]
		if { $dwellValue ne "" } {
			set_property DWELL_TIME $dwellValue [get_hw_sio_scans $xil_newScan]
		}
	}

	run_hw_sio_scan [get_hw_sio_scans $xil_newScan]
	wait_on_hw_sio_scan [get_hw_sio_scans $xil_newScan]
	write_hw_sio_scan -force $outputPath [get_hw_sio_scans $xil_newScan]
}

set argNames {
	outputPath
	hwServer
	serialNumber
	channelPath
	prbsBits
	loopback
	reportFile
	dwellMode
	dwellValue
}

if { $argc != [llength $argNames] } {
	puts "Incorrect argument count, got $argc, expected [llength $argNames]"
	puts "Usage: script.tcl $argNames"
	exit 1
}

for {set i 0} {$i < [llength $argNames]} {incr i} {
	set [lindex $argNames $i] [lindex $argv $i]
}

perform_eye_scan $outputPath $hwServer $serialNumber $channelPath $prbsBits $loopback $reportFile $dwellMode $dwellValue
