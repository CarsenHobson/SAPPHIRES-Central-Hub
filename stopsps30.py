from sps30 import SPS30

sps = SPS30(1)

def stop_sps30():
    sps.stop_measurement()
    
stop_sps30()
  
