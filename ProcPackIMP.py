
import sys, getopt, datetime, time, os
import dpkt
import pandas as pds, pyshark as psk

#Written by Landon Zweigle

# logarithm Base (default = 2)
LOG_BASE = 2 # math.e
##sys.setdefaultencoding('utf8')
entropy = 0
leng = 0

capDir = "./Captures/"


##This method has two parts
## First part allows for capture of packets on a specified ip address from command line
## Second part processes the captured packets-- this is what you are intersted.
## For  now, you can comment out the first few pieces of the code and use the remaining parts.
def Collect():
	ip = ""
	count = 100
	inFile =""
	outFile =""
	inter =""

	if(len(sys.argv) != 2):
		raise Excpetion("One (or more) arguments must be specified. The first arguement referse to the device being processed (for accessing arg0.pcap/csv)")

	try:
		try: ##gather pcap file name and storage file name
			opts, args = getopt.getopt(sys.argv[1:],"hi:c:",["ipaddress=","pcount=="])
		except getopt.GetoptError:
			sys.exit(1)
		for opt, arg in opts:
			if opt in ("-i","--ipaddress"):
				ip = arg
			elif opt in ("-c","--pcount"):
				count = arg
			else:
				print ("input error!")
				sys.exit(1)


		inFile = capDir + sys.argv[1] + '.pcap'
		storageName = capDir + sys.argv[1] + '.csv'
		pcap = psk.FileCapture(inFile)

		print('Capture file is [' + inFile + ']')
		print('Storage File is [' + storageName + ']')
		print('--------------------------')
		print('Starting Packet Header Parse...')

		os.system('touch ' + storageName)
		os.system('tshark -r ' + inFile + ' -T fields -e frame.number -e frame.protocols -e frame.len -e frame.packet_flags -e frame.time -e frame.time_relative -e eth.src -e eth.dst -e ip.src -e ip.dst -e ip.version -e ip.proto -e ip.ttl -e ip.hdr_len -e ip.len -e ip.id -e ip.flags -e ip.frag_offset -e ip.checksum -e tcp.seq -e tcp.ack -e tcp.srcport -e tcp.dstport -e tcp.hdr_len -e tcp.len -e tcp.flags -e tcp.options.timestamp.tsval -e tcp.options.timestamp.tsecr -e tcp.checksum -e tcp.window_size_value -e http.request.version -E header=y -E separator=, -E quote=d -E occurrence=f > ' + storageName)

		print('Header Parse Finished...')
		print('--------------------------')
		print('Calculating Packet Entropy')

		#load the parsed header into a DataFrame
		df = pds.read_csv(storageName, index_col=False)#.dropna(axis=1, how="all") #right now I dont know if I should keep the NA columns.

		#create the out DataFrame (csv)
		outDF = pds.DataFrame(columns=list(df.columns.values)+["Payload Entropy", "Payload Length"])
		print(df)
		print(outDF)

		print()

		#iterate over every packet in the dataframe df. Analyse it, and append the result to the output DataFrame (outdf).
		res = df.apply(tApply, axis=1, pcap=pcap)


		exit()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

		# open csv file and add "payload entropy" and "payload length" to columns

#		data = []
#		try:
#			row0 = csvR.next()
#			row0.append('Payload Entropy')
#			row0.append('Payload Length')
#			data.append(row0)
#		except StopIteration:
#			print ('No Rows')
#		except:
#			print ('Something else went wrong')

		# make pcapObject to parse the pcap file
#		p = pcap.pcapObject()
#		p.open_offline(inFile)
		try:
			for item in csvR:
				p.dispatch(1, analysepacket)
				item.append(entropy)
				item.append(leng)
				data.append(item)

		except KeyboardInterrupt:
			print ('interrupt')
		csvFile = open(storageName, 'w')
		csvW = csv.writer(csvFile)
		csvW.writerows(data)

		print('Finished Calcualting Packet Entropy')
		print('--------------------------')
		print('Sending Data to Storage')
		print('--------------------------')
		##os.system('scp ./' + storageName + ' ./' + inFile + ' jordantp@tokyo.cs.colostate.edu:/s/fir/e/nobackup/nuclear_iot/IOT')
		print('Finished Sending Data to Storage')
		print('--------------------------')
		sys.exit()
            
	except KeyboardInterrupt:
		print("Closing Program...")
		sys.exit()

def tApply(d, pcap):
#	if not pcap and not d:
#		return

	index = d.name
	packet = pcap[index]
	print(packet)
	#check if it is ipv4. This is essentially what extractpayload did.
	if(int(packet.eth.type,16) == 2048):
		decodeipv4(packet)
		


	#pktinfos, payload = extractpayload(dpkt.ethernet.Ethernet(data))

	#print(d)
	print("\nEE\n")

##Some basic processing we did for our paper
def analysepacket (pktlen, data, timestamp):
	if not data:
		return

	pktinfos, payload = extractpayload(dpkt.ethernet.Ethernet(data))

	if pktinfos and payload:
		global entropy 
		entropy = Entropy(payload)
		global leng 
		leng= len(payload)

def Entropy(data):
   # We determine the frequency of each byte
   # in the dataset and if this frequency is not null we use it for the
   # entropy calculation
	dataSize = len(data)
	ent = 0.0

	freq={}
	for c in data:
		if freq.has_key(c):
			freq[c] += 1
		else:
			freq[c] = 1

   # a byte can take 256 values from 0 to 255. Here we are looping 256 times
   # to determine if each possible value of a byte is in the dataset
	for key in freq.keys():
		f = float(freq[key])/dataSize
		if f > 0: # to avoid an error for log(0)
			ent = ent + f * math.log(f, LOG_BASE)

	return -ent

##This part is where packet processing happens
def decodeipv4(ip):
	pktinfos = dict()
	pktinfos['src_addr'] = pcap.ntoa(struct.unpack('i',ip.src)[0])
	pktinfos['dst_addr'] = pcap.ntoa(struct.unpack('i',ip.dst)[0])
	pktinfos['proto'] = ip.p

	if dpkt.ip.IP_PROTO_TCP == ip.p: #Check for TCP packets
		tcp = ip.data
		pktinfos['proto_name'] = 'TCP'
		pktinfos['src_port'] = tcp.sport
		pktinfos['dst_port'] = tcp.dport
		payload = tcp.data
	elif dpkt.ip.IP_PROTO_UDP == ip.p: #Check for UDP packets
		udp = ip.data
		pktinfos['proto_name'] = 'UDP'
		pktinfos['src_port'] = udp.sport
		pktinfos['dst_port'] = udp.dport
		payload = udp.data
	elif dpkt.ip.IP_PROTO_ICMP == ip.p: #Check for ICMP packets
		icmp = ip.data
		pktinfos['proto_name'] = 'ICMP'
		pktinfos['src_port'] = 0
		pktinfos['dst_port'] = 0
		payload = str(icmp.data)
	else:
		return None, None

	return pktinfos, payload

##This part should be of interest to you. This gives the payload.
def extractpayload(eth):
	if dpkt.ethernet.ETH_TYPE_IP == eth.type:      # ipv4 packet
		return decodeipv4(eth.data)
	elif dpkt.ethernet.ETH_TYPE_IP6 == eth.type:    # ipv6 packet
		return None, None
	elif dpkt.ethernet.ETH_TYPE_ARP == eth.type:    # arp packet
		return None, None
	elif dpkt.ethernet.ETH_TYPE_REVARP == eth.type:    # rarp packet
		return None, None
	else:
		return None, None



##This you can change or just change the Collect method to process a pcap file of your choice. Use Linux based python interpreter as it will have the pcap file.
def main():
	Collect()

if __name__ == "__main__":
	print("Running Main")
	main()
