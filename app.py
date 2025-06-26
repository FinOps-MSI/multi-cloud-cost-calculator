import streamlit as st
import pandas as pd
import re
from io import StringIO
import csv

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Cloud Cost Calculator",
    page_icon="☁️",
    layout="wide"
)

# --- Full, Embedded Pricing Data ---
# Data is stored in CSV format in multiline strings and parsed by pandas.
# This ensures every single row you provided is included.

EC2_DATA_STRING = """
Region,AWS Product Name,Instance Type,SUM of July Cost,vCPUs,Memory,Azure Service Tier,Azure Meter,AzureRegion,GCP Service Name,GCP SKU,GCP Region,AWS- On Demand Cost,AWS Monthly Cost,Azure Unit price,Azure Monthly Cost,GCP Unit Price,GCP Monthly Cost
us-gov-east-1,Amazon Elastic Compute Cloud,m6i.xlarge,$37,561.60,4,16 GiB,Virtual Machines,D4s v3,USGovVirginia,Compute Engine,n2-standard-4,#N/A,$0.21,$151.11,$0.55,$402.23,0,0
us-gov-east-1,Amazon Elastic Compute Cloud,g4dn.xlarge,$36,072.38,4,16 GiB,Virtual Machines,NC4as T4 v3,USGovVirginia,Compute Engine,g2-standard-4,#N/A,$0.57,$413.91,$0.66,$480.34,0,0
eu-west-1,Amazon Elastic Compute Cloud,g4dn.xlarge,$29,300.35,4,16 GiB,Virtual Machines,NC4as T4 v3,WestEurope,Compute Engine,g2-standard-4,europe-west4,$0.50,$366.46,$0.53,$383.98,0.7429,542.317
us-east-2,Amazon Elastic Compute Cloud,m5.4xlarge,$21,918.87,16,64 GiB,Virtual Machines,D16s v3,EastUS2,Compute Engine,n2-standard-16,us-east4,$0.66,$479.61,$0.61,$448.22,0.875,638.75
us-east-1,Amazon Elastic Compute Cloud,m5.4xlarge,$15,635.53,16,64 GiB,Virtual Machines,D16s v3,EastUS,Compute Engine,n2-standard-16,us-east4,$0.66,$479.61,$0.61,$448.22,0.875,638.75
eu-west-2,Amazon Elastic Compute Cloud,g4dn.xlarge,$14,683.90,4,16 GiB,Virtual Machines,NC4as T4 v3,UKWest,Compute Engine,g2-standard-4,europe-west2,$0.53,$383.98,$0.00,$0.00,0.8048,587.504
us-east-1,Amazon Elastic Compute Cloud,g4dn.xlarge,$13,069.36,4,16 GiB,Virtual Machines,NC4as T4 v3,EastUS,Compute Engine,g2-standard-4,us-east4,$0.45,$328.50,$0.42,$307.33,0.7045,514.285
us-east-2,Amazon Elastic Compute Cloud,t3.xlarge,$13,012.11,4,16 GiB,Virtual Machines,D4s v3,EastUS2,Compute Engine,n2-standard-4,us-east4,$0.14,$103.66,$0.15,$112.42,$0.22,160.79
us-west-2,Amazon Elastic Compute Cloud,m5.4xlarge,$9,591.52,16,64 GiB,Virtual Machines,D16s v3,WestUS2,Compute Engine,n2-standard-16,us-west1,$0.66,$479.61,$0.61,$448.22,0.7769,567.137
us-gov-east-1,Amazon Elastic Compute Cloud,g4dn.2xlarge,$9,258.90,8,32 GiB,Virtual Machines,NC8as T4 v3,USGovVirginia,Compute Engine,g2-standard-8,#N/A,$0.81,$592.03,$0.75,$548.96,0,0
us-east-1,Amazon Elastic Compute Cloud,g4dn.2xlarge,$8,300.83,8,32 GiB,Virtual Machines,NC8as T4 v3,EastUS,Compute Engine,g2-standard-8,us-east4,$0.64,$469.39,$0.60,$439.46,0.8536,623.128
us-east-1,Amazon Elastic Compute Cloud,t3.2xlarge,$6,997.06,8,192 GiB,Virtual Machines,D8s v3,EastUS,Compute Engine,n2-standard-8,us-east4,$0.29,$208.05,$0.91,$663.57,$0.44,321.58
us-east-1,Amazon Elastic Compute Cloud,m6i.xlarge,$6,550.38,4,17 GiB,Virtual Machines,D4s v3,EastUS,Compute Engine,n2-standard-4,us-east4,$0.16,$119.72,$0.46,$332.15,$0.22,160.79
eu-west-1,Amazon Elastic Compute Cloud,t3.xlarge,$6,415.79,4,16 GiB,Virtual Machines,D4s v3,WestEurope,Compute Engine,n2-standard-4,europe-west4,$0.16,$113.88,$0.19,$140.16,$0.20,142.79
us-east-1,Amazon Elastic Compute Cloud,t2.large,$6,092.11,2,36 GiB,Virtual Machines,B2ms,EastUS,Compute Engine,e2-standard-2,us-east4,$0.08,$57.67,$0.14,$102.20,0.067,48.91
us-east-1,Amazon Elastic Compute Cloud,m5.2xlarge,$5,964.55,8,32 GiB,Virtual Machines,D8s v3,EastUS,Compute Engine,n2-standard-8,us-east4,$0.33,$239.44,$0.91,$663.57,$0.44,321.58
us-west-2,Amazon Elastic Compute Cloud,t3.2xlarge,$5,065.17,8,192 GiB,Virtual Machines,D8s v3,WestUS2,Compute Engine,n2-standard-8,us-west1,$0.29,$208.05,$0.31,$224.11,$0.39,285.58
eu-west-1,Amazon Elastic Compute Cloud,m6i.4xlarge,$4,729.02,16,64 GiB,Virtual Machines,D16s v3,WestEurope,Compute Engine,n2-standard-16,europe-west4,$0.73,$534.36,$0.77,$560.64,0.8553,624.369
us-east-2,Amazon Elastic Compute Cloud,t3.2xlarge,$4,548.10,8,192 GiB,Virtual Machines,D8s v3,EastUS2,Compute Engine,n2-standard-8,us-east4,$0.29,$208.05,$0.60,$439.46,$0.44,321.58
us-west-2,Amazon Elastic Compute Cloud,t2.large,$4,501.18,2,36 GiB,Virtual Machines,B2ms,WestUS2,Compute Engine,e2-standard-2,us-west1,$0.08,$57.67,$0.14,$102.20,0.06769863,49.42
us-east-1,Amazon Elastic Compute Cloud,t3a.2xlarge,$4,200.15,8,32 GiB,Virtual Machines,B8as v2,EastUS,Compute Engine,e2-standard-8,us-east4,$0.26,$187.61,$0.24,$175.93,0.3019,220.387
eu-central-1,Amazon Elastic Compute Cloud,c6i.2xlarge,$4,065.82,8,16 GiB,Virtual Machines,F4s v2,GermanyWestCentral,Compute Engine,c2-standard-4,europe-west3,$0.33,$242.36,$0.16,$113.15,0.539,393.47
us-gov-east-1,Amazon Elastic Compute Cloud,t3.2xlarge,$3,694.41,8,192 GiB,Virtual Machines,D8s v3,USGovVirginia,Compute Engine,n2-standard-8,#N/A,$0.33,$243.82,$0.40,$294.19,0,0
us-gov-west-1,Amazon Elastic Compute Cloud,m5.4xlarge,$3,681.38,16,64 GiB,Virtual Machines,D16s v3,USGovVirginia,Compute Engine,n2-standard-16,#N/A,$0.83,$604.44,$1.20,$878.19,0,0
us-gov-west-1,Amazon Elastic Compute Cloud,m5.2xlarge,$3,680.39,8,32 GiB,Virtual Machines,D8s v3,USGovVirginia,Compute Engine,n2-standard-8,#N/A,$0.41,$302.22,$0.60,$439.46,0,0
us-east-1,Amazon Elastic Compute Cloud,t3.xlarge,$3,430.59,4,16 GiB,Virtual Machines,D4s v3,EastUS,Compute Engine,n2-standard-4,us-east4,$0.14,$103.66,$0.46,$332.15,$0.22,160.79
eu-west-1,Amazon Elastic Compute Cloud,g4dn.2xlarge,$3,381.58,8,32 GiB,Virtual Machines,NC8as T4 v3,WestEurope,Compute Engine,g2-standard-8,europe-west4,$0.72,$522.68,$0.75,$548.96,0.855,624.15
eu-west-2,Amazon Elastic Compute Cloud,m6i.xlarge,$3,378.62,4,18 GiB,Virtual Machines,D4s v3,UKWest,Compute Engine,n2-standard-4,europe-west2,$0.19,$138.70,$0.19,$135.78,$0.20,142.79
us-east-2,Amazon Elastic Compute Cloud,m5.2xlarge,$3,350.04,8,32 GiB,Virtual Machines,D8s v3,EastUS2,Compute Engine,n2-standard-8,us-east4,$0.33,$239.44,$0.60,$439.46,$0.44,321.58
us-east-2,Amazon Elastic Compute Cloud,r5.12xlarge,$3,314.76,48,384 GiB,Virtual Machines,E48s v3,EastUS2,Compute Engine,m1-megamem-96,us-east4,$2.59,$1,887.78,$2.42,$1,765.87,12.02268,8776.5564
us-east-1,Amazon Elastic Compute Cloud,t2.xlarge,$3,117.20,4,64 GiB,Virtual Machines,B4ms,EastUS,Compute Engine,e2-standard-4,us-east4,$0.16,$116.07,$0.28,$202.94,0.134,97.82
us-east-1,Amazon Elastic Compute Cloud,i4i.4xlarge,$3,077.71,16,128 GiB,Virtual Machines,L16s v3,EastUS,Compute Engine,n2-standard-16,us-east4,$1.17,$857.02,$1.11,$813.22,0.875,638.75
eu-west-2,Amazon Elastic Compute Cloud,t3a.medium,$2,558.58,2,4 GiB,Virtual Machines,B2as v2,UKWest,Compute Engine,e2-standard-2,europe-west2,$0.04,$26.28,$0.07,$53.29,0.068383562,49.92
ap-northeast-2,Amazon Elastic Compute Cloud,m5.4xlarge,$2,529.51,16,64 GiB,Virtual Machines,D16s v3,KoreaCentral,Compute Engine,n2-standard-16,asia-northeast3,$0.81,$589.11,$0.79,$574.51,0.9977,728.321
us-east-1,Amazon Elastic Compute Cloud,m5.large,$2,525.32,2,8 GiB,Virtual Machines,D2s_v3,EastUS,Compute Engine,n2-standard-2,us-east4,$0.08,$59.86,$0.08,$56.21,0.1094,79.862
us-east-1,Amazon Elastic Compute Cloud,c5.4xlarge,$2,300.67,16,32 GiB,Virtual Machines,F16s v2,EastUS,Compute Engine,c2-standard-16,us-east4,$0.58,$424.13,$0.54,$395.66,0.9406,686.638
us-gov-west-1,Amazon Elastic Compute Cloud,r5.2xlarge,$2,297.06,8,64 GiB,Virtual Machines,E8s v3,USGovVirginia,Compute Engine,n2-highmem-8,#N/A,$0.52,$376.68,$0.70,$509.54,0,0
us-east-2,Amazon Elastic Compute Cloud,g4dn.2xlarge,$2,287.93,8,32 GiB,Virtual Machines,NC8as T4 v3,EastUS2,Compute Engine,g2-standard-8,us-east4,$0.64,$469.39,$0.60,$439.46,0.8536,623.128
us-east-2,Amazon Elastic Compute Cloud,t2.xlarge,$2,275.99,4,64 GiB,Virtual Machines,B4ms,EastUS2,Compute Engine,e2-standard-4,us-east4,$0.16,$116.07,$0.13,$97.09,0.134,97.82
eu-west-2,Amazon Elastic Compute Cloud,m5.2xlarge,$2,270.70,8,32 GiB,Virtual Machines,D8s v3,UKWest,Compute Engine,n2-standard-8,europe-west2,$0.38,$277.40,$0.37,$271.56,0.391205479,285.58
us-west-2,Amazon Elastic Compute Cloud,m5.xlarge,$2,268.20,4,16 GiB,Virtual Machines,D4s v3,WestUS2,Compute Engine,n2-standard-4,us-west1,$0.16,$119.72,$0.15,$112.42,$0.20,142.79
us-east-1,Amazon Elastic Compute Cloud,m4.2xlarge,$2,260.38,8,32 GiB,Virtual Machines,D8s_v3,EastUS,Compute Engine,n2-standard-8,us-east4,$0.34,$249.66,$0.31,$224.11,$0.44,321.58
ap-northeast-3,Amazon Elastic Compute Cloud,m5.4xlarge,$2,227.59,16,64 GiB,Virtual Machines,D16s v3,JapanWest,Compute Engine,n2-standard-16,#N/A,$0.85,$619.04,$0.83,$602.98,0,0
us-east-1,Amazon Elastic Compute Cloud,t2.2xlarge,$2,207.68,8,32 GiB,Virtual Machines,B8ms,EastUS,Compute Engine,e2-standard-8,us-east4,$0.32,$231.41,$0.56,$407.34,0.3019,220.387
us-east-1,Amazon Elastic Compute Cloud,m5.xlarge,$2,166.12,4,16 GiB,Virtual Machines,D4s v3,EastUS,Compute Engine,n2-standard-4,us-east4,$0.16,$119.72,$0.46,$332.15,$0.22,160.79
us-east-2,Amazon Elastic Compute Cloud,m5.xlarge,$2,098.29,4,16 GiB,Virtual Machines,D4s v3,EastUS2,Compute Engine,n2-standard-4,us-east4,$0.16,$119.72,$0.15,$112.42,$0.22,160.79
us-east-1,Amazon Elastic Compute Cloud,m5a.4xlarge,$2,072.79,16,64 GiB,Virtual Machines,D16as_v4,EastUS,Compute Engine,n2-standard-16,us-east4,$0.59,$429.24,$0.61,$448.22,0.875,638.75
us-east-1,Amazon Elastic Compute Cloud,c5.2xlarge,$2,061.06,8,16 GiB,Virtual Machines,F8s v2,EastUS,Compute Engine,c2-standard-8,us-east4,$0.29,$212.43,$0.79,$577.43,$0.47,345.52
us-east-1,Amazon Elastic Compute Cloud,c4.xlarge,$2,000.79,4,7.5 GiB,Virtual Machines,F4s_v2,EastUS,Compute Engine,c2-standard-4,us-east4,$0.17,$124.10,$0.14,$98.55,$0.24,172.76
us-east-2,Amazon Elastic Compute Cloud,c4.4xlarge,$1,941.21,16,30 GiB,Virtual Machines,F16s_v2,EastUS2,Compute Engine,c2-standard-16,us-east4,$0.68,$497.13,$0.54,$395.66,0.9406,686.638
eu-west-2,Amazon Elastic Compute Cloud,m5.4xlarge,$1,931.90,16,64 GiB,Virtual Machines,D16s v3,UKWest,Compute Engine,n2-standard-16,europe-west2,$0.76,$554.07,$0.74,$543.12,0.778315068,568.17
us-east-2,Amazon Elastic Compute Cloud,r5.2xlarge,$1,916.73,8,64 GiB,Virtual Machines,E8s v3,EastUS2,Compute Engine,n2-highmem-8,us-east4,$0.43,$314.63,$0.43,$310.98,0.59018,430.8314
us-east-2,Amazon Elastic Compute Cloud,r5.xlarge,$1,870.93,4,32 GiB,Virtual Machines,E4s v3,EastUS2,Compute Engine,n2-highmem-4,us-east4,$0.22,$156.95,$0.21,$155.49,0.29509,215.4157
us-gov-west-1,Amazon Elastic Compute Cloud,m5.xlarge,$1,840.21,4,16 GiB,Virtual Machines,D4s v3,USGovVirginia,Compute Engine,n2-standard-4,#N/A,$0.21,$151.11,$0.30,$219.73,0,0
ap-southeast-1,Amazon Elastic Compute Cloud,m5.4xlarge,$1,827.10,16,64 GiB,Virtual Machines,D16s v3,SoutheastAsia,Compute Engine,n2-standard-16,asia-southeast1,$0.82,$599.33,$0.80,$584.00,0.9584,699.632
us-east-2,Amazon Elastic Compute Cloud,c5.4xlarge,$1,759.33,16,32 GiB,Virtual Machines,F16s v2,EastUS2,Compute Engine,c2-standard-16,us-east4,$0.58,$424.13,$0.54,$395.66,0.9406,686.638
us-west-1,Amazon Elastic Compute Cloud,m5.2xlarge,$1,704.04,8,32 GiB,Virtual Machines,D8s v3,WestUS,Compute Engine,n2-standard-8,#N/A,$0.38,$279.59,$0.37,$273.02,0,0
us-east-1,Amazon Elastic Compute Cloud,c5.large,$1,604.36,2,4 GiB,Virtual Machines,F2s v2,EastUS,Compute Engine,c2-standard-4,us-east4,$0.07,$53.29,$0.07,$49.64,$0.24,172.76
us-east-2,Amazon Elastic Compute Cloud,t2.large,$1,515.99,2,36 GiB,Virtual Machines,B2ms,EastUS2,Compute Engine,e2-standard-2,us-east4,$0.08,$57.67,$0.07,$48.91,0.067,48.91
us-east-2,Amazon Elastic Compute Cloud,c5.large,$1,509.31,2,4 GiB,Virtual Machines,F2s v2,EastUS2,Compute Engine,c2-standard-4,us-east4,$0.07,$53.29,$0.07,$49.64,$0.24,172.76
us-west-1,Amazon Elastic Compute Cloud,t3.xlarge,$1,508.29,4,16 GiB,Virtual Machines,D4s v3,WestUS,Compute Engine,n2-standard-4,#N/A,$0.17,$124.10,$0.19,$136.51,0,0
us-east-1,Amazon Elastic Compute Cloud,c5.xlarge,$1,358.46,4,8 GiB,Virtual Machines,F4s v2,EastUS,Compute Engine,c2-standard-4,us-east4,$0.15,$105.85,$0.40,$289.08,$0.24,172.76
sa-east-1,Amazon Elastic Compute Cloud,m5.4xlarge,$1,266.29,16,64 GiB,Virtual Machines,D16s v3,BrazilSouth,Compute Engine,n2-standard-16,southamerica-east1,$1.05,$764.31,$1.02,$743.14,1.2333,900.309
us-west-1,Amazon Elastic Compute Cloud,t3.2xlarge,$1,256.94,8,192 GiB,Virtual Machines,D8s v3,WestUS,Compute Engine,n2-standard-8,#N/A,$1.05,$764.31,$0.37,$273.02,0,0
us-west-2,Amazon Elastic Compute Cloud,t3.xlarge,$1,161.08,4,16 GiB,Virtual Machines,D4s v3,WestUS2,Compute Engine,n2-standard-4,us-west1,$0.14,$103.66,$0.15,$112.42,$0.20,142.79
eu-west-2,Amazon Elastic Compute Cloud,r5.2xlarge,$1,116.83,8,64 GiB,Virtual Machines,E8s v3,UKWest,Compute Engine,n2-highmem-8,europe-west2,$0.51,$369.38,$0.50,$364.27,0.67515,492.8595
ap-northeast-2,Amazon Elastic Compute Cloud,t3.2xlarge,$1,115.06,8,32 GiB,Virtual Machines,D8s v3,KoreaCentral,Compute Engine,n2-standard-8,asia-northeast3,$0.36,$259.88,$0.39,$287.62,0.391205479,285.58
us-east-2,Amazon Elastic Compute Cloud,m4.2xlarge,$1,094.78,8,32 GiB,Virtual Machines,D8s_v3,EastUS2,Compute Engine,n2-standard-8,us-east4,$0.34,$249.66,$0.31,$224.11,$0.44,321.58
us-east-1,Amazon Elastic Compute Cloud,c4.4xlarge,$1,009.30,16,30 GiB,Virtual Machines,F16s_v2,EastUS,Compute Engine,c2-standard-16,us-east4,$0.68,$497.13,$0.54,$395.66,0.9406,686.638
ap-southeast-1,Amazon Elastic Compute Cloud,t3.xlarge,$983.92,4,16 GiB,Virtual Machines,D4s v3,SoutheastAsia,Compute Engine,n2-standard-4,asia-southeast1,$0.18,$132.13,$0.55,$399.31,$0.20,142.79
us-west-2,Amazon Elastic Compute Cloud,c5.4xlarge,$862.47,16,32 GiB,Virtual Machines,F16s v2,WestUS2,Compute Engine,c2-standard-16,us-west1,$0.58,$424.13,$0.54,$395.66,0.8352,609.696
eu-west-1,Amazon Elastic Compute Cloud,m6i.xlarge,$855.81,4,19 GiB,Virtual Machines,D4s v3,WestEurope,Compute Engine,n2-standard-4,europe-west4,$0.18,$133.59,$0.19,$140.16,$0.20,142.79
ap-northeast-3,Amazon Elastic Compute Cloud,t3.2xlarge,$855.29,8,32 GiB,Virtual Machines,D8s v3,JapanWest,Compute Engine,n2-standard-8,#N/A,$0.37,$271.56,$0.41,$301.49,0,0
us-west-1,Amazon Elastic Compute Cloud,m5.xlarge,$851.28,4,16 GiB,Virtual Machines,D4s v3,WestUS,Compute Engine,n2-standard-4,#N/A,$0.19,$140.16,$0.19,$136.51,0,0
eu-central-1,Amazon Elastic Compute Cloud,c5.xlarge,$835.26,4,8 GiB,Virtual Machines,F4s v2,GermanyWestCentral,Compute Engine,c2-standard-4,europe-west3,$0.17,$121.18,$0.16,$113.15,0.539,393.47
ap-northeast-1,Amazon Elastic Compute Cloud,t3.xlarge,$827.73,4,16 GiB,Virtual Machines,D4s v3,JapanEast,Compute Engine,n2-standard-4,asia-northeast1,$0.19,$135.78,$0.21,$150.38,$0.20,142.79
us-east-2,Amazon Elastic Compute Cloud,m5.large,$809.17,2,8 GiB,Virtual Machines,D2s_v3,EastUS2,Compute Engine,n2-standard-2,us-east4,$0.08,$59.86,$0.08,$56.21,0.1094,79.862
us-west-1,Amazon Elastic Compute Cloud,c5.2xlarge,$807.72,8,16 GiB,Virtual Machines,F8s v2,WestUS,Compute Engine,c2-standard-8,#N/A,$0.36,$264.99,$0.34,$247.47,0,0
ap-southeast-1,Amazon Elastic Compute Cloud,t3.2xlarge,$803.20,8,192 GiB,Virtual Machines,D8s v3,SoutheastAsia,Compute Engine,n2-standard-8,asia-southeast1,$0.36,$263.53,$0.40,$292.00,0.391205479,285.58
eu-central-1,Amazon Elastic Compute Cloud,c5.2xlarge,$797.04,8,16 GiB,Virtual Machines,F8s v2,GermanyWestCentral,Compute Engine,c2-standard-8,europe-west3,$0.33,$242.36,$0.31,$226.30,0.539,393.47
us-gov-east-1,Amazon Elastic Compute Cloud,m5.xlarge,$766.60,4,16 GiB,Virtual Machines,D4s v3,USGovVirginia,Compute Engine,n2-standard-4,#N/A,$0.21,$151.11,$0.55,$402.23,0,0
us-gov-east-1,Amazon Elastic Compute Cloud,t3.xlarge,$735.12,4,16 GiB,Virtual Machines,D4s v3,USGovVirginia,Compute Engine,n2-standard-4,#N/A,$0.17,$121.91,$0.55,$402.23,0,0
ap-northeast-3,Amazon Elastic Compute Cloud,t3.xlarge,$708.65,4,16 GiB,Virtual Machines,D4s v3,JapanWest,Compute Engine,n2-standard-4,#N/A,$0.19,$135.78,$0.21,$150.38,0,0
eu-central-1,Amazon Elastic Compute Cloud,c5.large,$697.05,2,4 GiB,Virtual Machines,F2s v2,GermanyWestCentral,Compute Engine,c2-standard-2,europe-west3,$0.08,$60.59,$0.08,$56.94,0.117,85.41
us-east-1,Amazon Elastic Compute Cloud,r5.2xlarge,$638.62,8,64 GiB,Virtual Machines,E8s v3,EastUS,Compute Engine,n2-highmem-8,us-east4,$0.43,$314.63,$0.40,$294.19,0.59018,430.8314
us-west-2,Amazon Elastic Compute Cloud,r5.2xlarge,$638.62,8,64 GiB,Virtual Machines,E8s v3,WestUS2,Compute Engine,n2-highmem-8,us-west1,$0.43,$314.63,$0.40,$294.19,0.52406,382.5638
us-gov-west-1,Amazon Elastic Compute Cloud,t3.xlarge,$618.60,4,16 GiB,Virtual Machines,D4s v3,USGovVirginia,Compute Engine,n2-standard-4,#N/A,$0.17,$121.91,$0.30,$219.73,0,0
us-east-1,Amazon Elastic Compute Cloud,c6i.2xlarge,$609.39,8,16 GiB,Virtual Machines,F4s v2,EastUS,Compute Engine,c2-standard-4,us-east4,$0.29,$212.43,$0.40,$289.08,$0.24,172.76
us-west-1,Amazon Elastic Compute Cloud,g4dn.2xlarge,$571.47,8,32 GiB,Virtual Machines,NC8as T4 v3,WestUS,Compute Engine,g2-standard-8,#N/A,$0.77,$562.83,$0.72,$527.06,0,0
eu-central-1,Amazon Elastic Compute Cloud,m5.xlarge,$559.46,4,16 GiB,Virtual Machines,D4s v3,GermanyWestCentral,Compute Engine,n2-standard-4,europe-west3,$0.20,$143.81,$0.18,$134.32,$0.20,142.79
ap-northeast-2,Amazon Elastic Compute Cloud,t3.xlarge,$557.53,4,16 GiB,Virtual Machines,D4s v3,KoreaCentral,Compute Engine,n2-standard-4,asia-northeast3,$0.18,$129.94,$0.20,$143.81,$0.20,142.79
sa-east-1,Amazon Elastic Compute Cloud,t3.2xlarge,$556.15,8,192 GiB,Virtual Machines,D8s v3,BrazilSouth,Compute Engine,n2-standard-8,southamerica-east1,$0.46,$335.80,$0.51,$371.57,0.391205479,285.58
us-west-2,Amazon Elastic Compute Cloud,t2.xlarge,$526.89,4,64 GiB,Virtual Machines,B4ms,WestUS2,Compute Engine,e2-standard-4,us-west1,$0.16,$116.07,$0.28,$202.94,0.13539726,98.84
us-west-2,Amazon Elastic Compute Cloud,m5.2xlarge,$486.90,8,32 GiB,Virtual Machines,D8s v3,WestUS2,Compute Engine,n2-standard-8,us-west1,$0.33,$239.44,$0.31,$224.11,$0.39,285.58
us-east-2,Amazon Elastic Compute Cloud,c6i.2xlarge,$412.16,8,16 GiB,Virtual Machines,F4s v2,EastUS2,Compute Engine,c2-standard-4,us-east4,$0.29,$212.43,$0.14,$98.55,$0.24,172.76
us-west-2,Amazon Elastic Compute Cloud,m4.2xlarge,$388.43,8,32 GiB,Virtual Machines,D8s_v3,WestUS2,Compute Engine,n2-standard-8,us-west1,$0.34,$249.66,$0.31,$224.11,$0.39,285.58
eu-west-2,Amazon Elastic Compute Cloud,t3.xlarge,$384.68,4,16 GiB,Virtual Machines,D4s v3,UKWest,Compute Engine,n2-standard-4,europe-west2,$0.16,$117.53,$0.19,$135.78,$0.20,142.79
eu-central-1,Amazon Elastic Compute Cloud,t3.xlarge,$383.98,4,16 GiB,Virtual Machines,D4s v3,GermanyWestCentral,Compute Engine,n2-standard-4,europe-west3,$0.16,$119.72,$0.18,$134.32,$0.20,142.79
ap-southeast-2,Amazon Elastic Compute Cloud,m5.xlarge,$368.26,4,16 GiB,Virtual Machines,D4s v3,AustraliaEast,Compute Engine,n2-standard-4,australia-southeast1,$0.21,$149.65,$0.18,$134.32,$0.20,142.79
us-west-1,Amazon Elastic Compute Cloud,r5.xlarge,$355.04,4,32 GiB,Virtual Machines,E4s v3,WestUS,Compute Engine,n2-highmem-4,#N/A,$0.24,$174.47,$0.24,$173.01,0,0
sa-east-1,Amazon Elastic Compute Cloud,t3.xlarge,$354.09,4,16 GiB,Virtual Machines,D4s v3,BrazilSouth,Compute Engine,n2-standard-4,southamerica-east1,$0.23,$167.90,$0.25,$185.42,$0.20,142.79
eu-west-2,Amazon Elastic Compute Cloud,t3a.2xlarge,$318.09,8,32 GiB,Virtual Machines,B8as v2,UKWest,Compute Engine,e2-standard-8,europe-west2,$0.29,$212.43,$0.29,$212.43,0.34534,252.0982
eu-central-1,Amazon Elastic Compute Cloud,c4.xlarge,$287.63,4,7.5 GiB,Virtual Machines,F4s_v2,GermanyWestCentral,Compute Engine,c2-standard-4,europe-west3,$0.19,$141.62,$0.16,$113.15,0.539,393.47
us-east-2,Amazon Elastic Compute Cloud,t3a.2xlarge,$283.07,8,32 GiB,Virtual Machines,B8as v2,EastUS2,Compute Engine,e2-standard-8,us-east4,$0.26,$187.61,$0.24,$175.93,0.3019,220.387
us-east-2,Amazon Elastic Compute Cloud,c5.2xlarge,$272.18,8,16 GiB,Virtual Machines,F8s v2,EastUS2,Compute Engine,c2-standard-8,us-east4,$0.29,$212.43,$0.27,$197.10,$0.47,345.52
eu-west-2,Amazon Elastic Compute Cloud,m4.2xlarge,$264.23,8,32 GiB,Virtual Machines,D8s_v3,UKWest,Compute Engine,n2-standard-8,europe-west2,$0.40,$289.81,$0.37,$271.56,0.391205479,285.58
us-east-2,Amazon Elastic Compute Cloud,c4.xlarge,$252.15,4,7.5 GiB,Virtual Machines,F4s_v2,EastUS2,Compute Engine,c2-standard-4,us-east4,$0.17,$124.10,$0.14,$98.55,$0.24,172.76
eu-central-1,Amazon Elastic Compute Cloud,t2.large,$240.16,2,36 GiB,Virtual Machines,B2ms,GermanyWestCentral,Compute Engine,e2-standard-2,europe-west3,$0.09,$67.16,$0.08,$56.21,0.068383562,49.92
eu-central-1,Amazon Elastic Compute Cloud,c5.4xlarge,$238.53,16,32 GiB,Virtual Machines,F16s v2,GermanyWestCentral,Compute Engine,c2-standard-16,europe-west3,$0.66,$483.99,$0.62,$453.33,1.076,785.48
us-west-1,Amazon Elastic Compute Cloud,c5.large,$233.11,2,4 GiB,Virtual Machines,F2s v2,WestUS,Compute Engine,c2-standard-4,#N/A,$0.09,$66.43,$0.09,$62.05,0,0
us-east-2,Amazon Elastic Compute Cloud,c5.xlarge,$219.22,4,8 GiB,Virtual Machines,F4s v2,EastUS2,Compute Engine,c2-standard-4,us-east4,$0.15,$105.85,$0.14,$98.55,$0.24,172.76
eu-central-1,Amazon Elastic Compute Cloud,m5.2xlarge,$208.65,8,32 GiB,Virtual Machines,D8s v3,GermanyWestCentral,Compute Engine,n2-standard-8,europe-west3,$0.39,$286.89,$0.37,$268.64,0.391205479,285.58
us-east-1,Amazon Elastic Compute Cloud,t3a.medium,$192.01,2,4 GiB,Virtual Machines,B2as v2,EastUS,Compute Engine,e2-standard-2,us-east4,$0.03,$23.36,$0.07,$49.64,0.067,48.91
us-east-2,Amazon Elastic Compute Cloud,t2.2xlarge,$169.97,8,32 GiB,Virtual Machines,B8ms,EastUS2,Compute Engine,e2-standard-8,us-east4,$0.32,$231.41,$0.27,$194.18,0.3019,220.387
ap-southeast-2,Amazon Elastic Compute Cloud,m5.2xlarge,$160.06,8,32 GiB,Virtual Machines,D8s v3,AustraliaEast,Compute Engine,n2-standard-8,australia-southeast1,$0.41,$299.30,$0.00,$0.00,0.391205479,285.58
ap-southeast-2,Amazon Elastic Compute Cloud,c5.large,$128.61,2,4 GiB,Virtual Machines,F2s v2,AustraliaEast,Compute Engine,c2-standard-4,australia-southeast1,$0.10,$69.35,$0.00,$0.00,0.210178082,153.43
us-west-2,Amazon Elastic Compute Cloud,m5.large,$121.72,2,8 GiB,Virtual Machines,D2s_v3,WestUS2,Compute Engine,n2-standard-2,us-west1,$0.08,$59.86,$0.08,$56.21,0.0971,70.883
us-west-2,Amazon Elastic Compute Cloud,c4.xlarge,$120.50,4,7.5 GiB,Virtual Machines,F4s_v2,WestUS2,Compute Engine,c2-standard-4,us-west1,$0.17,$124.10,$0.14,$98.55,$0.21,153.43
eu-west-2,Amazon Elastic Compute Cloud,t2.2xlarge,$115.93,8,32 GiB,Virtual Machines,B8ms,UKWest,Compute Engine,e2-standard-8,europe-west2,$0.36,$263.53,$0.30,$219.73,0.34534,252.0982
eu-central-1,Amazon Elastic Compute Cloud,m5.large,$96.85,2,8 GiB,Virtual Machines,D2s_v3,GermanyWestCentral,Compute Engine,n2-standard-2,europe-west3,$0.10,$71.54,$0.09,$67.16,0.19560274,142.79
eu-west-2,Amazon Elastic Compute Cloud,t2.large,$94.54,2,36 GiB,Virtual Machines,B2ms,UKWest,Compute Engine,e2-standard-2,europe-west2,$0.09,$65.70,$0.08,$54.75,0.068383562,49.92
ap-southeast-2,Amazon Elastic Compute Cloud,m5.large,$93.72,2,8 GiB,Virtual Machines,D2s_v3,AustraliaEast,Compute Engine,n2-standard-2,australia-southeast1,$0.10,$75.19,$0.00,$0.00,0.19560274,142.79
eu-west-1,Amazon Elastic Compute Cloud,c5.2xlarge,$86.02,8,16 GiB,Virtual Machines,F8s v2,WestEurope,Compute Engine,c2-standard-8,europe-west4,$0.33,$239.44,$0.31,$226.30,0.46,335.8
eu-west-2,Amazon Elastic Compute Cloud,t3.2xlarge,$74.06,8,192 GiB,Virtual Machines,D8s v3,UKWest,Compute Engine,n2-standard-8,europe-west2,$0.32,$235.79,$0.37,$271.56,0.391205479,285.58
eu-south-1,Amazon Elastic Compute Cloud,c5.xlarge,$71.78,4,8 GiB,Virtual Machines,F4s v2,USGovVirginia,Compute Engine,c2-standard-4,#N/A,$0.17,$126.29,$0.00,$0.00,0,0
eu-west-2,Amazon Elastic Compute Cloud,c5.4xlarge,$70.39,16,32 GiB,Virtual Machines,F16s v2,UKWest,Compute Engine,c2-standard-16,europe-west2,$0.69,$504.43,$0.65,$472.31,1.076,785.48
us-west-2,Amazon Elastic Compute Cloud,c5.xlarge,$64.96,4,8 GiB,Virtual Machines,F4s v2,WestUS2,Compute Engine,c2-standard-4,us-west1,$0.15,$105.85,$0.14,$98.55,$0.21,153.43
us-east-2,Amazon Elastic Compute Cloud,t3a.medium,$62.27,2,4 GiB,Virtual Machines,B2as v2,EastUS2,Compute Engine,e2-standard-2,us-east4,$0.03,$23.36,$0.06,$43.80,0.067,48.91
eu-west-2,Amazon Elastic Compute Cloud,c5.large,$56.66,2,4 GiB,Virtual Machines,F2s v2,UKWest,Compute Engine,c2-standard-4,europe-west2,$0.09,$62.78,$0.08,$59.13,0.210178082,153.43
ap-southeast-1,Amazon Elastic Compute Cloud,m5.large,$55.09,2,8 GiB,Virtual Machines,D2s_v3,SoutheastAsia,Compute Engine,n2-standard-2,asia-southeast1,$0.10,$75.19,$0.10,$73.00,0.19560274,142.79
ap-southeast-1,Amazon Elastic Compute Cloud,c5.xlarge,$34.84,4,8 GiB,Virtual Machines,F4s v2,SoutheastAsia,Compute Engine,c2-standard-4,asia-southeast1,$0.17,$122.64,$0.16,$114.61,0.258,188.34
eu-west-2,Amazon Elastic Compute Cloud,c5.2xlarge,$32.94,8,16 GiB,Virtual Machines,F8s v2,UKWest,Compute Engine,c2-standard-8,europe-west2,$0.35,$251.85,$0.32,$236.52,0.539,393.47
eu-west-1,Amazon Elastic Compute Cloud,c5.large,$24.49,2,4 GiB,Virtual Machines,F2s v2,WestEurope,Compute Engine,c2-standard-4,europe-west4,$0.08,$59.86,$0.08,$56.94,0.210178082,153.43
us-east-1,Amazon Elastic Compute Cloud,m6i.4xlarge,$17.37,16,64 GiB,Virtual Machines,D16s v3,EastUS,Compute Engine,n2-standard-16,us-east4,$0.66,$479.61,$0.61,$448.22,0.875,638.75
eu-central-1,Amazon Elastic Compute Cloud,t3.2xlarge,$8.26,8,192 GiB,Virtual Machines,D8s v3,GermanyWestCentral,Compute Engine,n2-standard-8,europe-west3,$0.66,$479.61,$0.37,$268.64,0.391205479,285.58
eu-west-2,Amazon Elastic Compute Cloud,m5.xlarge,$8.21,4,16 GiB,Virtual Machines,D4s v3,UKWest,Compute Engine,n2-standard-4,europe-west2,$0.19,$138.70,$0.19,$135.78,$0.20,142.79
ap-southeast-2,Amazon Elastic Compute Cloud,t3.xlarge,$5.42,4,16 GiB,Virtual Machines,D4s v3,AustraliaEast,Compute Engine,n2-standard-4,australia-southeast1,$0.18,$132.13,$0.18,$134.32,$0.20,142.79
sa-east-1,Amazon Elastic Compute Cloud,c5.large,$2.93,2,4 GiB,Virtual Machines,F2s v2,BrazilSouth,Compute Engine,c2-standard-4,southamerica-east1,$0.11,$81.76,$0.11,$76.65,0.210178082,153.43
eu-central-1,Amazon Elastic Compute Cloud,t3a.medium,$1.16,2,4 GiB,Virtual Machines,B2as v2,GermanyWestCentral,Compute Engine,e2-standard-2,europe-west3,$0.04,$27.01,$0.07,$50.37,0.068383562,49.92
"""

RDS_DATA_STRING="""
Cloud Type,AWS Product Name,Meter,Database Engine,Region,Pricing Term,vCPUs,Memory,Cloud Type,Service Name,Azure Tier,Meter,AzureRegion,Pricing Term,AWS Unit Price,AWS- On Demand Monthly Cost,Azure Unit Price,Azure Monthly Cost,Azure Projected Cost,Cloud Type,GCP Service Name,GCP SKU,GCP Region,Cloud SQL Edition,vCPUs,Memory,GCP Unit Price,GCP Ondemand Cost/month
AWS,Amazon Relational Database Service,db.r6i.16xlarge,Aurora PostgreSQL,eu-west-1,OnDemand,64,512 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 32 vCore,WestEurope,1 Hr,8.7552,6391.296,3.648,2663.04,$8,109.50,GCP,Cloud SQL,db-perf-optimized-N-64,europe-west2,Enterprise Plus,64,512 GiB,$9.73,$7,103.15
AWS,Amazon Relational Database Service,db.r5.8xlarge,Aurora MySQL,us-west-2,OnDemand,32,256 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 32 vCore,WestUS2,1 Hr,3.9672,2896.056,3.7792,2758.816,$8,401.17,GCP,Cloud SQL,db-perf-optimized-N-32,us-west1,Enterprise Plus,32,256 GiB,$4.07,$2,972.04
AWS,Amazon Relational Database Service,db.m5.4xlarge,MariaDB,us-east-2,OnDemand,16,64 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 16 vCore,EastUS2,1 Hr,1.16964,853.8372,1.6816,1227.568,$10,176.18,GCP,Cloud SQL,,us-east4,,16,64 GiB,,
AWS,Amazon Relational Database Service,db.r5.2xlarge,Aurora PostgreSQL,us-east-2,OnDemand,8,64 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 8 vCore,EastUS2,1 Hr,0.9918,724.014,0.904,659.92,$4,019.18,GCP,Cloud SQL,db-perf-optimized-N-8,us-east4,Enterprise Plus,8,64 GiB,$1.11,$806.59
AWS,Amazon Relational Database Service,db.r5.2xlarge,Aurora PostgreSQL,us-west-2,OnDemand,8,64 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 8 vCore,WestUS2,1 Hr,0.9918,724.014,0.752,548.96,$3,342.09,GCP,Cloud SQL,db-perf-optimized-N-8,us-west1,Enterprise Plus,8,64 GiB,$1.04,$755.76
AWS,Amazon Relational Database Service,db.m5.4xlarge,MariaDB,us-gov-west-1,OnDemand,16,64 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 16 vCore,USGovVirginia,1 Hr,1.64,1197.2,$1.75,$1,279,$4,446.08,GCP,Cloud SQL,,us-west1,,16,64 GiB,,
AWS,Amazon Relational Database Service,db.r5.4xlarge,MariaDB,us-east-2,OnDemand,16,128 GiB,Azure,Azure Database for MariaDB,Memory Optimized,Gen 5, 16 vCore,EastUS2,1 Hr,1.6416,1198.368,2.2688,1656.224,$5,043.55,GCP,Cloud SQL,,us-east4,,16,128 GiB,,
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,us-east-2,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,EastUS2,1 Hr,0.146205,106.72965,0.2102,153.446,$4,884.08,GCP,Cloud SQL,,us-east4,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.m5.2xlarge,MariaDB,us-east-2,OnDemand,8,32 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 8 vCore,EastUS2,1 Hr,0.58482,426.9186,0.8408,613.784,$4,826.48,GCP,Cloud SQL,,us-east4,,8,32 GiB,,
AWS,Amazon Relational Database Service,db.r5.2xlarge,Aurora PostgreSQL,us-east-1,OnDemand,8,64 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 8 vCore,EastUS,1 Hr,0.9918,724.014,0.752,548.96,$1,963.12,GCP,Cloud SQL,db-perf-optimized-N-8,us-east4,Enterprise Plus,8,64 GiB,$1.11,$806.59
AWS,Amazon Relational Database Service,db.m5.2xlarge,MySQL,us-east-1,OnDemand,8,32 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 8 vCore,EastUS,1 Hr,0.58482,426.9186,0.684,499.32,$2,027.38,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,8,32 GiB,$0.62,$451.52
AWS,Amazon Relational Database Service,db.m5.xlarge,MariaDB,us-east-2,OnDemand,4,16 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 4 vCore,EastUS2,1 Hr,0.29241,213.4593,0.4204,306.892,$2,492.14,GCP,Cloud SQL,,us-east4,,4,16 GiB,,
AWS,Amazon Relational Database Service,db.r5.large,Aurora MySQL,us-gov-east-1,OnDemand,2,16 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 2 vCore,USGovVirginia,1 Hr,0.29925,218.4525,0.289,210.97,$1,285.76,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,us-gov-west-1,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.205,149.65,$0.22,$160,$1,112.39,GCP,Cloud SQL,,us-west1,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.r5.2xlarge,Aurora MySQL,us-gov-east-1,OnDemand,8,64 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 8 vCore,USGovVirginia,1 Hr,1.197,873.81,1.156,843.88,$857.75,GCP,Cloud SQL,db-perf-optimized-N-8,us-east4,Enterprise Plus,8,64 GiB,$0.77,$561.02
AWS,Amazon Relational Database Service,db.t3.large,Aurora PostgreSQL,us-gov-west-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.196,143.08,$0.22,$160,$978.41,GCP,Cloud SQL,db-standard-2,us-west1,Enterprise,2,8 GiB,$0.16,$115.62
AWS,Amazon Relational Database Service,db.m6i.4xlarge,MySQL,us-east-1,OnDemand,16,64 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 16 vCore,EastUS,1 Hr,1.16964,853.8372,1.368,998.64,$1,013.68,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,16,64 GiB,$1.21,$884.85
AWS,Amazon Relational Database Service,db.t3.large,Aurora PostgreSQL,sa-east-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,BrazilSouth,1 Hr,0.28728,209.7144,0.184,134.32,$480.34,GCP,Cloud SQL,db-standard-2,southamerica-east1,Enterprise,2,8 GiB,$0.19,$138.81
AWS,Amazon Relational Database Service,db.r4.xlarge,MySQL,us-gov-west-1,OnDemand,4,30.5 GiB,Azure,Azure Database for MySQL,Memory optimized,Gen 5, 4 vCore,USGovVirginia,1 Hr,0.578,421.94,$0.35,$128,$222.48,GCP,Cloud SQL,db-perf-optimized-N-4,us-west1,Enterprise Plus,4,30.5 GiB,$0.53,$386.38
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,us-west-1,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,WestUS,1 Hr,0.166725,121.70925,0.2048,149.504,$899.57,GCP,Cloud SQL,,us-west2,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.r5.large,Aurora MySQL,eu-central-1,OnDemand,2,16 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 2 vCore,GermanyWestCentral,1 Hr,0.29925,218.4525,0.2858,208.634,$635.33,GCP,Cloud SQL,db-perf-optimized-N-2,europe-west3,Enterprise Plus,2,16 GiB,$0.33,$241.74
AWS,Amazon Relational Database Service,db.m5.xlarge,MySQL,ap-southeast-2,OnDemand,4,16 GiB,Azure,Azure Database for MySQL,General Purpose,D series, 4 vCore,AustraliaEast,1 Hr,0.40185,293.3505,0.47,343.1,$696.54,GCP,Cloud SQL,db-standard-4,australia-southeast1,Enterprise,4,16 GiB,$0.40,$289.91
AWS,Amazon Relational Database Service,db.r5.large,Aurora MySQL,us-west-2,OnDemand,2,16 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 2 vCore,WestUS2,1 Hr,0.24795,181.0035,0.2362,172.426,$525.07,GCP,Cloud SQL,db-perf-optimized-N-2,us-west1,Enterprise Plus,2,16 GiB,$0.28,$201.60
AWS,Amazon Relational Database Service,db.m5.xlarge,PostgreSQL,eu-central-1,OnDemand,4,32 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 4 vCore,GermanyWestCentral,1 Hr,0.36252,264.6396,0.3336,243.528,$494.39,GCP,Cloud SQL,db-perf-optimized-N-4,europe-west3,Enterprise Plus,4,32 GiB,$0.63,$463.07
AWS,Amazon Relational Database Service,db.t3.large,MariaDB,us-east-2,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,Basic,Gen 5, 2 vCore,EastUS2,1 Hr,0.11628,84.8844,0.0816,59.568,$362.79,GCP,Cloud SQL,,us-east4,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.m6i.large,PostgreSQL,us-east-2,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS2,1 Hr,0.15219,111.0987,0.1682,122.786,$493.69,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.r4.large,Aurora MySQL,us-gov-west-1,OnDemand,2,15.25 GiB,Azure,Azure Database for MySQL,Memory optimized,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.35,255.5,$0.18,$128,$222.48,GCP,Cloud SQL,db-perf-optimized-N-2,us-west1,Enterprise Plus,2,15.25 GiB,$0.28,$201.60
AWS,Amazon Relational Database Service,db.t3.xlarge,PostgreSQL,us-gov-west-1,OnDemand,4,16 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 4 vCore,USGovVirginia,1 Hr,0.392,286.16,$0.44,$320,$496.61,GCP,Cloud SQL,db-standard-4,us-west1,Enterprise,4,16 GiB,$0.29,$214.25
AWS,Amazon Relational Database Service,db.m4.2xlarge,MySQL,us-west-2,OnDemand,8,32 GiB,Azure,Azure Database for MySQL,General Purpose,D series, 8 vCore,WestUS2,1 Hr,0.5985,436.905,0.684,499.32,$506.85,GCP,Cloud SQL,Custom machine type,us-west1,Enterprise,8,32 GiB,$0.58,$421.71
AWS,Amazon Relational Database Service,db.m5.2xlarge,MySQL,us-west-2,OnDemand,8,32 GiB,Azure,Azure Database for MySQL,General Purpose,D series, 8 vCore,WestUS2,1 Hr,0.58482,426.9186,0.684,499.32,$506.84,GCP,Cloud SQL,Custom machine type,us-west1,Enterprise,8,32 GiB,$0.58,$421.71
AWS,Amazon Relational Database Service,db.r5.xlarge,Aurora PostgreSQL,eu-west-1,OnDemand,4,32 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 4 vCore,WestEurope,1 Hr,0.5472,399.456,0.456,332.88,$340.03,GCP,Cloud SQL,db-perf-optimized-N-4,europe-west2,Enterprise Plus,4,32 GiB,$0.63,$463.07
AWS,Amazon Relational Database Service,db.t3.large,Aurora PostgreSQL,ca-central-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,CanadaCentral,1 Hr,0.1539,112.347,0.154,112.42,$402.02,GCP,Cloud SQL,db-standard-2,northamerica-northeast1,Enterpise,2,8 GiB,$0.19,$138.81
AWS,Amazon Relational Database Service,db.m6i.2xlarge,PostgreSQL,us-east-1,OnDemand,8,32 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 8 vCore,EastUS,1 Hr,0.60876,444.3948,0.568,414.64,$356.84,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,8,32 GiB,$0.62,$451.52
AWS,Amazon Relational Database Service,db.m5d.large,PostgreSQL,us-east-2,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS2,1 Hr,0.17955,131.0715,0.1682,122.786,$347.20,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.r5.large,Aurora PostgreSQL,us-east-1,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 2 vCore,EastUS,1 Hr,0.24795,181.0035,0.188,137.24,$278.61,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.r5.large,Aurora PostgreSQL,us-east-2,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 2 vCore,EastUS2,1 Hr,0.24795,181.0035,0.226,164.98,$334.93,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.t3.large,Aurora PostgreSQL,us-east-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.14022,102.3606,0.1402,102.346,$366.00,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.t3.medium,Aurora PostgreSQL,us-east-2,OnDemand,2,4 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS2,1 Hr,0.07011,51.1803,0.1682,122.786,$878.19,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,4 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.r5.xlarge,Aurora PostgreSQL,us-east-1,OnDemand,4,32 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 4 vCore,EastUS,1 Hr,0.4959,362.007,0.376,274.48,$275.18,GCP,Cloud SQL,db-perf-optimized-N-4,us-east4,Enterprise Plus,4,32 GiB,$0.57,$412.39
AWS,Amazon Relational Database Service,db.m5.xlarge,PostgreSQL,sa-east-1,OnDemand,4,16 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 4 vCore,BrazilSouth,1 Hr,0.39843,290.8539,0.368,268.64,$272.69,GCP,Cloud SQL,db-standard-4,southamerica-east1,Enterprise,4,16 GiB,$0.35,$257.21
AWS,Amazon Relational Database Service,db.m5.2xlarge,PostgreSQL,us-east-1,OnDemand,8,32 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 8 vCore,EastUS,1 Hr,0.60876,444.3948,0.568,414.64,$271.08,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,8,32 GiB,$0.62,$451.52
AWS,Amazon Relational Database Service,db.t2.large,PostgreSQL,us-east-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.123975,90.50175,0.1402,102.346,$311.67,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.m5.large,PostgreSQL,us-gov-west-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.205,149.65,$0.22,$160,$291.67,GCP,Cloud SQL,db-standard-2,us-west1,Enterprise,2,8 GiB,$0.16,$115.62
AWS,Amazon Relational Database Service,db.m5d.large,PostgreSQL,us-east-1,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.17955,131.0715,0.1402,102.346,$207.28,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.m5.xlarge,MySQL,us-gov-west-1,OnDemand,4,16 GiB,Azure,Azure Database for MySQL,General Purpose,Gen 5, 4 vCore,USGovVirginia,1 Hr,0.41,299.3,$0.35,$256,$222.48,GCP,Cloud SQL,Custom machine type,us-west1,Enterprise,4,16 GiB,$0.30,$219.36
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,eu-central-1,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,GermanyWestCentral,1 Hr,0.173565,126.70245,0.2084,152.132,$308.84,GCP,Cloud SQL,,europe-west3,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,eu-west-2,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,UKWest,1 Hr,0.16929,123.5817,0.2032,148.336,$301.15,GCP,Cloud SQL,,europe-west2,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.t3.medium,Aurora MySQL,us-east-2,OnDemand,2,4 GiB,Azure,Azure Database for MySQL,Burstable,B2s, 2 vCore,EastUS2,1 Hr,0.07011,51.1803,0.068,49.64,$236.69,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,2,4 GiB,$0.14,$104.62
AWS,Amazon Relational Database Service,db.m6i.large,PostgreSQL,us-east-1,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.15219,111.0987,0.1402,102.346,$198.97,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.t3.large,PostgreSQL,us-east-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.123975,90.50175,0.1402,102.346,$207.78,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.m5.large,MySQL,us-east-2,OnDemand,2,8 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 2 vCore,EastUS2,1 Hr,0.146205,106.72965,0.171,124.83,$166.35,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,2,8 GiB,$0.17,$126.52
AWS,Amazon Relational Database Service,db.t2.medium,Aurora MySQL,us-gov-west-1,OnDemand,2,4 GiB,Azure,Azure Database for MySQL,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.098,71.54,$0.18,$128,$222.47,GCP,Cloud SQL,db-lightweight-2,us-west1,Enterprise,2,4 GiB,$0.13,$96.46
AWS,Amazon Relational Database Service,db.m5.large,PostgreSQL,us-west-2,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestUS2,1 Hr,0.15219,111.0987,0.1402,102.346,$103.89,GCP,Cloud SQL,db-standard-2,us-west1,Enterprise,2,8 GiB,$0.16,$115.62
AWS,Amazon Relational Database Service,db.t2.small,Aurora MySQL,eu-west-1,OnDemand,1,2 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,WestEurope,1 Hr,0.03762,27.4626,0.0199,14.527,$58.99,GCP,Cloud SQL,db-g1-small,europe-west2,Enterprise,1,2 GiB,$0.05,$38.80
AWS,Amazon Relational Database Service,db.t3.large,Aurora PostgreSQL,eu-west-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestEurope,1 Hr,0.15048,109.8504,0.166,121.18,$123.01,GCP,Cloud SQL,db-standard-2,europe-west2,Enterprise,2,8 GiB,$0.19,$138.81
AWS,Amazon Relational Database Service,db.m4.large,MySQL,us-east-1,OnDemand,2,8 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 2 vCore,EastUS,1 Hr,0.149625,109.22625,0.171,124.83,$126.71,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,2,8 GiB,$0.17,$126.52
AWS,Amazon Relational Database Service,db.t2.micro,MySQL,us-east-1,OnDemand,1,1 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,EastUS,1 Hr,0.014535,10.61055,0.017,12.41,$125.96,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,1,1 GiB,$0.10,$70.99
AWS,Amazon Relational Database Service,db.t2.small,MySQL,us-east-1,OnDemand,1,2 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,EastUS,1 Hr,0.02907,21.2211,0.017,12.41,$62.98,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,1,2 GiB,$0.10,$70.99
AWS,Amazon Relational Database Service,db.t3.large,PostgreSQL,eu-west-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestEurope,1 Hr,0.13338,97.3674,0.166,121.18,$123.00,GCP,Cloud SQL,db-standard-2,europe-west2,Enterprise,2,8 GiB,$0.19,$138.81
AWS,Amazon Relational Database Service,db.t3.small,PostgreSQL,us-gov-west-1,OnDemand,2,2 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.049,35.77,$0.22,$160,$368.89,GCP,Cloud SQL,db-lightweight-2,us-west1,Enterprise,2,2 GiB,$0.13,$96.46
AWS,Amazon Relational Database Service,db.r5.large,Aurora MySQL,us-east-1,OnDemand,2,16 GiB,Azure,Azure Database for MySQL,Business Critical,E Series, 2 vCore,EastUS,1 Hr,0.24795,181.0035,0.2362,172.426,$64.24,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.t3.medium,Aurora MySQL,us-west-1,OnDemand,2,4 GiB,Azure,Azure Database for MySQL,Burstable,B2s, 2 vCore,WestUS,1 Hr,0.09063,66.1599,0.088,64.24,$65.21,GCP,Cloud SQL,db-lightweight-2,us-west2,Enterprise,2,4 GiB,$0.16,$115.81
AWS,Amazon Relational Database Service,db.t3.medium,MySQL,ap-southeast-2,OnDemand,2,4 GiB,Azure,Azure Database for MySQL,Burstable,B2s, 2 vCore,AustraliaEast,1 Hr,0.08892,64.9116,0.104,75.92,$77.06,GCP,Cloud SQL,Custom Machine type,australia-southeast1,Enterprise,2,4 GiB,$0.18,$132.16
AWS,Amazon Relational Database Service,db.t3.small,MySQL,ap-southeast-2,OnDemand,2,2 GiB,Azure,Azure Database for MySQL,Burstable,B2s, 2 vCore,AustraliaEast,1 Hr,0.04446,32.4558,0.104,75.92,$154.13,GCP,Cloud SQL,Custom Machine type,australia-southeast1,Enterprise,2,2 GiB,$0.18,$130.42
AWS,Amazon Relational Database Service,db.t2.small,Aurora MySQL,us-west-2,OnDemand,1,2 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,WestUS2,1 Hr,0.035055,25.59015,0.017,12.41,$24.46,GCP,Cloud SQL,db-g1-small,us-west1,Enterprise,1,2 GiB,$0.04,$32.33
AWS,Amazon Relational Database Service,db.m5.large,MySQL,us-west-1,OnDemand,2,8 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 2 vCore,WestUS,1 Hr,0.166725,121.70925,0.195,142.35,$57.87,GCP,Cloud SQL,db-standard-2,us-west2,Enterprise,2,8 GiB,$0.19,$138.81
AWS,Amazon Relational Database Service,db.t3.medium,PostgreSQL,eu-west-1,OnDemand,2,4 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestEurope,1 Hr,0.06669,48.6837,0.166,121.18,$123.01,GCP,Cloud SQL,db-lightweight-2,europe-west2,Enterprise,2,4 GiB,$0.16,$115.81
AWS,Amazon Relational Database Service,db.m4.large,PostgreSQL,us-east-1,OnDemand,2,8 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.15561,113.5953,0.1402,102.346,$41.08,GCP,Cloud SQL,db-standard-2,us-east4,Enterprise,2,8 GiB,$0.17,$123.78
AWS,Amazon Relational Database Service,db.t3.small,MySQL,us-west-2,OnDemand,1,2 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,WestUS2,1 Hr,0.02907,21.2211,0.017,12.41,$25.19,GCP,Cloud SQL,db-g1-small,us-west1,Enterprise,1,2 GiB,$0.04,$32.33
AWS,Amazon Relational Database Service,db.m5.large,MySQL,us-east-1,OnDemand,2,8 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 2 vCore,EastUS,1 Hr,0.146205,106.72965,0.171,124.83,$46.51,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,2,8 GiB,$0.17,$126.52
AWS,Amazon Relational Database Service,db.r5.large,Aurora PostgreSQL,eu-west-1,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 2 vCore,WestEurope,1 Hr,0.2736,199.728,0.228,166.44,$27.15,GCP,Cloud SQL,db-perf-optimized-N-2,europe-west2,Enterprise Plus,2,16 GiB,$0.33,$241.74
AWS,Amazon Relational Database Service,db.t3.micro,MariaDB,us-east-2,OnDemand,2,1 GiB,Azure,Azure Database for MariaDB,Basic,Gen 5, 2 vCore,EastUS2,1 Hr,0.014535,10.61055,0.0816,59.568,$181.39,GCP,Cloud SQL,,us-east4,,2,1 GiB,,
AWS,Amazon Relational Database Service,db.m5.large,MariaDB,ap-southeast-2,OnDemand,2,8 GiB,Azure,Azure Database for MariaDB,General Purpose,Gen 5, 2 vCore,,1 Hr,0.200925,146.67525,0.2468,180.164,$34.01,GCP,Cloud SQL,,australia-southeast1,,2,8 GiB,,
AWS,Amazon Relational Database Service,db.r5d.large,PostgreSQL,us-east-1,OnDemand,2,16 GiB,Azure,Microsoft Azure PostgreSQL,Memory Optimized,Gen 5, 2 vCore,EastUS,1 Hr,0.24453,178.5069,0.188,137.24,$19.89,GCP,Cloud SQL,db-perf-optimized-N-2,us-east4,Enterprise Plus,2,16 GiB,$0.30,$215.29
AWS,Amazon Relational Database Service,db.t2.micro,MySQL,us-gov-west-1,OnDemand,2,1 GiB,Azure,Azure Database for MySQL,General Purpose,Gen 5, 2 vCore,USGovVirginia,1 Hr,0.02,14.6,$0.18,$128,$222.51,GCP,Cloud SQL,db-lightweight-2,us-west1,Enterprise,2,1 GiB,$0.13,$96.46
AWS,Amazon Relational Database Service,db.t3.micro,PostgreSQL,eu-west-1,OnDemand,2,1 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestEurope,1 Hr,0.0171,12.483,0.166,121.18,$245.99,GCP,Cloud SQL,db-lightweight-2,europe-west2,Enterprise,2,1 GiB,$0.16,$115.81
AWS,Amazon Relational Database Service,db.t3.small,PostgreSQL,eu-west-1,OnDemand,2,2 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestEurope,1 Hr,0.033345,24.34185,0.166,121.18,$123.01,GCP,Cloud SQL,db-lightweight-2,europe-west2,Enterprise,2,2 GiB,$0.16,$115.81
AWS,Amazon Relational Database Service,db.m5.xlarge,MySQL,us-east-1,OnDemand,4,16 GiB,Azure,Azure Database for MySQL,General Purpose,D Series, 4 vCore,EastUS,1 Hr,0.29241,213.4593,0.342,249.66,$27.71,GCP,Cloud SQL,db-standard-4,us-east4,Enterprise,4,16 GiB,$0.31,$229.38
AWS,Amazon Relational Database Service,db.t2.micro,PostgreSQL,us-east-1,OnDemand,2,1 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.01539,11.2347,0.1402,102.346,$207.79,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,1 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.t2.small,PostgreSQL,us-east-1,OnDemand,2,2 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.03078,22.4694,0.1402,102.346,$103.90,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,2 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.t3.small,PostgreSQL,us-east-1,OnDemand,2,2 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.03078,22.4694,0.1402,102.346,$103.90,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,2 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.t3.micro,MySQL,us-east-1,OnDemand,1,1 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,EastUS,1 Hr,0.014535,10.61055,0.017,12.41,$26.62,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,1,1 GiB,$0.10,$70.99
AWS,Amazon Relational Database Service,db.t2.small,MySQL,us-west-2,OnDemand,1,2 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 1 vCore,WestUS2,1 Hr,0.02907,21.2211,0.017,12.41,$12.60,GCP,Cloud SQL,db-g1-small,us-west1,Enterprise,1,2 GiB,$0.04,$32.33
AWS,Amazon Relational Database Service,db.t3.small,MariaDB,us-east-2,OnDemand,2,2 GiB,Azure,Azure Database for MariaDB,Basic,Gen 5, 2 vCore,EastUS2,1 Hr,0.02907,21.2211,0.0816,59.568,$60.46,GCP,Cloud SQL,,us-east4,,2,2 GiB,,
AWS,Amazon Relational Database Service,db.t3.medium,Aurora MySQL,us-east-1,OnDemand,2,4 GiB,Azure,Azure Database for MySQL,Burstable,B1MS, 2 vCore,EastUS,1 Hr,0.07011,51.1803,0.068,49.64,$18.81,GCP,Cloud SQL,Custom machine type,us-east4,Enterprise,2,4 GiB,$0.14,$104.62
AWS,Amazon Relational Database Service,db.t3.medium,PostgreSQL,us-east-1,OnDemand,2,4 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.06156,44.9388,0.1402,102.346,$38.40,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,4 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.m6i.xlarge,PostgreSQL,us-east-1,OnDemand,4,16 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 4 vCore,EastUS,1 Hr,0.30438,222.1974,0.2804,204.692,$11.63,GCP,Cloud SQL,db-standard-4,us-east4,Enterprise,4,16 GiB,$0.31,$229.38
AWS,Amazon Relational Database Service,db.t3.micro,PostgreSQL,us-west-2,OnDemand,2,1 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,WestUS2,1 Hr,0.01539,11.2347,0.1402,102.346,$103.85,GCP,Cloud SQL,db-lightweight-2,us-west1,Enterprise,2,1 GiB,$0.13,$96.46
AWS,Amazon Relational Database Service,db.t3.micro,PostgreSQL,us-east-1,OnDemand,2,1 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.01539,11.2347,0.1402,102.346,$99.75,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,1 GiB,$0.14,$103.25
AWS,Amazon Relational Database Service,db.t2.micro,MariaDB,us-east-1,OnDemand,2,1 GiB,Azure,Azure Database for MariaDB,Burstable,Gen 5, 2 vCore,EastUS,1 Hr,0.014535,10.61055,0.1752,127.896,$129.82,GCP,Cloud SQL,,us-east4,,2,1 GiB,,
AWS,Amazon Relational Database Service,db.t3.medium,Aurora PostgreSQL,us-east-1,OnDemand,2,4 GiB,Azure,Microsoft Azure PostgreSQL,General Purpose,Gen 5, 2 vCore,EastUS,1 Hr,0.07011,51.1803,0.1402,102.346,$20.16,GCP,Cloud SQL,db-lightweight-2,us-east4,Enterprise,2,4 GiB,$0.14,$103.25
"""

S3_DATA_STRING="""
Cloud Type,AWS Product Name,Meter,Region,Pricing Unit,AWS Ondemand Cost,Cloud Type,Meter,Region,Azure Ondemand Cost,Cloud Type,GCP Service Name,Meter,Region,GCP Ondemand Cost
AWS,Amazon Simple Storage Service,Standard,us-east-1,1 GB,$0.02,Azure,Blob Storage- Hot,EastUS,$0.02,GCP,Cloud Storage,Standard,us-east4,0.02
AWS,Amazon Simple Storage Service,Standard,us-gov-west-1,1 GB,$0.04,Azure,Blob Storage- Hot,USGovVirginia,$0.03,GCP,Cloud Storage,Standard,us-west1,0.0176
AWS,Amazon Simple Storage Service,Standard,us-east-2,1 GB,$0.02,Azure,Blob Storage- Hot,EastUS2,$0.02,GCP,Cloud Storage,Standard,us-east4,0.02
AWS,Amazon Simple Storage Service,Standard,eu-west-1,1 GB,$0.02,Azure,Blob Storage- Hot,WestEurope,$0.03,GCP,Cloud Storage,Standard,europe-west2,0.02
AWS,Amazon Simple Storage Service,Standard,us-west-1,1 GB,$0.03,Azure,Blob Storage- Hot,WestUS,$0.03,GCP,Cloud Storage,Standard,us-west2,0.02
AWS,Amazon Simple Storage Service,Standard,eu-west-2,1 GB,$0.02,Azure,Blob Storage- Hot,UKWest,$0.01,GCP,Cloud Storage,Standard,europe-west2,0.02
AWS,Amazon Simple Storage Service,Glacier Deep Archive,us-east-1,1 GB,$0.00,Azure,Blob Storage- Archive,EastUS,$0.01,GCP,Cloud Storage,Archive Storage,us-east4,0.0023
AWS,Amazon Simple Storage Service,Standard,us-west-2,1 GB,$0.02,Azure,Blob Storage- Hot,WestUS2,$0.03,GCP,Cloud Storage,Standard,us-west1,0.0176
AWS,Amazon Simple Storage Service,Standard - Infrequent Access,us-east-1,1 GB,$0.01,Azure,Blob Storage- Cool,EastUS,$0.03,GCP,Cloud Storage,Nearline Storage,us-east4,0.01
AWS,Amazon Simple Storage Service,One Zone - Infrequent Access,us-east-1,1 GB,$0.01,Azure,Blob Storage- Cool,EastUS,$0.03,GCP,Cloud Storage,Nearline Storage,us-east4,0.01
AWS,Amazon Simple Storage Service,Standard,eu-central-1,1 GB,$0.02,Azure,Blob Storage- Hot,GermanyWestCentral,$0.01,GCP,Cloud Storage,Standard,europe-west3,0.02
AWS,Amazon Simple Storage Service,Glacier Instant Retrieval,us-east-1,1 GB,$0.00,Azure,Blob Storage- Cold,EastUS,$0.03,GCP,Cloud Storage,Coldline Storage,us-east4,0.0047
AWS,Amazon Simple Storage Service,Standard,eu-west-2,1 GB,$0.02,Azure,Blob Storage- Hot,UKWest,$0.01,GCP,Cloud Storage,Standard,europe-west2,0.02
AWS,Amazon Simple Storage Service,Standard,ap-southeast-2,1 GB,$0.03,Azure,Blob Storage- Hot,AustraliaEast,$0.03,GCP,Cloud Storage,Standard,australia-southeast1,0.02
AWS,Amazon Simple Storage Service,Standard - Infrequent Access,eu-central-1,1 GB,$0.01,Azure,Blob Storage- Cool,GermanyWestCentral,$0.01,GCP,Cloud Storage,Nearline Storage,europe-west3,0.01
AWS,Amazon Simple Storage Service,Glacier Instant Retrieval,eu-central-1,1 GB,$0.01,Azure,Blob Storage- Cold,GermanyWestCentral,$0.01,GCP,Cloud Storage,Coldline Storage,europe-west3,0.0056
AWS,Amazon Simple Storage Service,Standard,eu-south-1,1 GB,$0.02,Azure,Blob Storage- Hot,ItalyNorth,$0.01,GCP,Cloud Storage,Standard,europe-west8,0.02
AWS,Amazon Simple Storage Service,Glacier Instant Retrieval,ap-southeast-1,1 GB,$0.01,Azure,Blob Storage- Cold,SoutheastAsia,$0.01,GCP,Cloud Storage,Coldline Storage,asia-southeast1,0.0047
AWS,Amazon Simple Storage Service,Standard,sa-east-1,1 GB,$0.02,Azure,Blob Storage- Hot,BrazilSouth,$0.02,GCP,Cloud Storage,Standard,southamerica-east1,0.03
AWS,Amazon Simple Storage Service,Standard,ca-central-1,1 GB,$0.03,Azure,Blob Storage- Hot,CanadaCentral,$0.01,GCP,Cloud Storage,Standard,northamerica-northeast1,0.02
AWS,Amazon Simple Storage Service,Standard,us-gov-east-1,1 GB,$0.04,Azure,Blob Storage- Hot,USGovVirginia,$0.03,GCP,Cloud Storage,Standard,us-east4,0.02
AWS,Amazon Simple Storage Service,Standard - Infrequent Access,ap-southeast-1,1 GB,$0.01,Azure,Blob Storage- Cool,SoutheastAsia,$0.01,GCP,Cloud Storage,Nearline Storage,asia-southeast1,0.01
AWS,Amazon Simple Storage Service,Amazon Glacier,eu-west-2,1 GB,$0.00,Azure,Blob Storage- Archive,UKWest,$0.01,GCP,Cloud Storage,Archive Storage,europe-west2,0.0023
AWS,Amazon Simple Storage Service,Amazon Glacier,ca-central-1,1 GB,$0.00,Azure,Blob Storage- Archive,CanadaCentral,$0.01,GCP,Cloud Storage,Archive Storage,northamerica-northeast1,0.0023
AWS,Amazon Simple Storage Service,Standard,ap-southeast-2,1 GB,$0.03,Azure,Blob Storage- Hot,AustraliaEast,$0.03,GCP,Cloud Storage,Standard,australia-southeast1,0.02
"""

# Helper functions for parsing
def parse_memory(mem_str):
    if isinstance(mem_str, (int, float)): return mem_str
    if isinstance(mem_str, str):
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", mem_str)
        if numbers: return float(numbers[0])
    return 0

def parse_cost(cost_str):
    if isinstance(cost_str, (int, float)): return float(cost_str)
    if isinstance(cost_str, str):
        try: return float(str(cost_str).replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError): return 0.0
    return 0.0

@st.cache_data(ttl="1h")
def load_and_process_data(ec2_csv_str, rds_csv_str, s3_csv_str):
    """
    Loads and normalizes the complete dataset from the embedded strings.
    FIX: Uses pandas.read_csv which correctly handles complex CSV formats with
    quoted fields, preventing parsing errors.
    """
    try:
        # --- Process EC2 Data ---
        ec2_df = pd.read_csv(StringIO(ec2_csv_str))
        ec2_data = []
        for _, row in ec2_df.iterrows():
            vcpu = int(float(row['vCPUs']))
            memory = parse_memory(row['Memory'])
            
            if pd.notna(row['AWS Monthly Cost']) and parse_cost(row['AWS Monthly Cost']) > 0:
                ec2_data.append({'cloud': 'aws', 'region': row['Region'], 'meter': row['Instance Type'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['AWS Monthly Cost'])})
            if pd.notna(row['Azure Monthly Cost']) and parse_cost(row['Azure Monthly Cost']) > 0:
                ec2_data.append({'cloud': 'azure', 'region': row['AzureRegion'], 'meter': row['Azure Meter'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['Azure Monthly Cost'])})
            if pd.notna(row.get('GCP Monthly Cost')) and row.get('GCP Region') != '#N/A' and parse_cost(row['GCP Monthly Cost']) > 0:
                ec2_data.append({'cloud': 'gcp', 'region': row['GCP Region'], 'meter': row['GCP SKU'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['GCP Monthly Cost'])})

        # --- Process RDS Data ---
        rds_df = pd.read_csv(StringIO(rds_csv_str))
        rds_data = []
        for _, row in rds_df.iterrows():
            if pd.notna(row['AWS- On Demand Monthly Cost']) and parse_cost(row['AWS- On Demand Monthly Cost']) > 0:
                rds_data.append({'cloud': 'aws', 'meter': row['Meter'], 'region': row['Region'], 'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']), 'cost': parse_cost(row['AWS- On Demand Monthly Cost'])})
            if pd.notna(row['Azure Monthly Cost']) and parse_cost(row['Azure Monthly Cost']) > 0:
                rds_data.append({'cloud': 'azure', 'meter': row['Meter.1'], 'region': row['AzureRegion'], 'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']), 'cost': parse_cost(row['Azure Monthly Cost'])})
            if pd.notna(row.get('GCP SKU')) and pd.notna(row.get('GCP Ondemand Cost/month')) and parse_cost(row.get('GCP Ondemand Cost/month')) > 0:
                 rds_data.append({'cloud': 'gcp', 'meter': row['GCP SKU'], 'region': row['GCP Region'], 'vcpu': int(float(row['vCPUs.1'])), 'memory': parse_memory(row['Memory.1']), 'cost': parse_cost(row['GCP Ondemand Cost/month'])})

        # --- Process S3 Data ---
        s3_df = pd.read_csv(StringIO(s3_csv_str))
        s3_data = []
        for _, row in s3_df.iterrows():
            if parse_cost(row['AWS Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'aws', 'tier': row['Meter'], 'region': row['Region'], 'costPerGB': parse_cost(row['AWS Ondemand Cost'])})
            if parse_cost(row['Azure Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'azure', 'tier': row['Meter.1'], 'region': row['Region.1'], 'costPerGB': parse_cost(row['Azure Ondemand Cost'])})
            if parse_cost(row['GCP Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'gcp', 'tier': row['Meter.2'], 'region': row['Region.2'], 'costPerGB': parse_cost(row['GCP Ondemand Cost'])})
        
        # Remove duplicates
        processed_ec2 = [dict(t) for t in {tuple(d.items()) for d in ec2_data}]
        processed_rds = [dict(t) for t in {tuple(d.items()) for d in rds_data}]
        processed_s3 = [dict(t) for t in {tuple(d.items()) for d in s3_data}]

        return {'ec2': processed_ec2, 'rds': processed_rds, 's3': processed_s3}
    except Exception as e:
        st.error(f"An error occurred while processing the data. Please check the data format. Error: {e}")
        return None


# Load the data by calling the cached function
RAW_DATA = load_and_process_data(EC2_DATA_STRING, RDS_DATA_STRING, S3_DATA_STRING)

# --- Helper Functions ---
def find_equivalent(primary_instance, service_type):
    if not primary_instance or not RAW_DATA: return {}
    data = RAW_DATA[service_type]
    
    aws_equiv = next((i for i in data if i['cloud'] == 'aws' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)
    azure_equiv = next((i for i in data if i['cloud'] == 'azure' and i.get('vcpu') == primary_instance.get('vcpu')), None) # Simplified Azure matching
    gcp_equiv = next((i for i in data if i['cloud'] == 'gcp' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)
    
    # Fill in the primary instance itself if it wasn't found as an equivalent
    if not aws_equiv and primary_instance.get('cloud') == 'aws': aws_equiv = primary_instance
    if not azure_equiv and primary_instance.get('cloud') == 'azure': azure_equiv = primary_instance
    if not gcp_equiv and primary_instance.get('cloud') == 'gcp': gcp_equiv = primary_instance
    
    return {'aws': aws_equiv, 'azure': azure_equiv, 'gcp': gcp_equiv}

def get_s3_equivalents(primary_tier, storage_gb):
    if not RAW_DATA: return {}
    equivalents = {}
    
    aws_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'aws' and t.get('tier') == primary_tier), None)
    # Match S3 tiers more loosely (e.g., 'Standard' matches 'Blob Storage- Hot')
    azure_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'azure' and primary_tier.split(' ')[0] in t.get('tier', '')), None)
    gcp_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'gcp' and primary_tier.split(' ')[0] in t.get('tier', '')), None)

    if aws_tier: equivalents['aws'] = {**aws_tier, 'cost': aws_tier['costPerGB'] * storage_gb}
    if azure_tier: equivalents['azure'] = {**azure_tier, 'cost': azure_tier['costPerGB'] * storage_gb}
    if gcp_tier: equivalents['gcp'] = {**gcp_tier, 'cost': gcp_tier['costPerGB'] * storage_gb}
    return equivalents

# --- Main App UI ---
st.title("☁️ Multi-Cloud Cost Calculator")
st.write("Compare costs for equivalent services across AWS, Azure, and GCP.")

if not RAW_DATA:
    st.error("Data could not be loaded. Please check that the data strings are pasted correctly.")
    st.stop()

if 'comparison_set' not in st.session_state:
    st.session_state.comparison_set = None
    st.session_state.quantity = 1

with st.container(border=True):
    st.header("Service Configuration")
    cols = st.columns(5)
    with cols[0]:
        service_type_map = {
            'Virtual Machine (EC2)': 'ec2',
            'Managed Database (RDS)': 'rds',
            'Object Storage (S3)': 's3'
        }
        service_type_label = st.selectbox("Service Type", service_type_map.keys(), key='service_type_label')
        service_type = service_type_map[service_type_label]

    if service_type in ['ec2', 'rds']:
        with cols[1]:
            available_regions = sorted(list(set(item['region'] for item in RAW_DATA[service_type])))
            selected_region = st.selectbox("Region", available_regions, key=f'{service_type}_region')
        with cols[2]:
            instances_in_region = [item for item in RAW_DATA[service_type] if item['region'] == selected_region]
            instance_options = {item['meter']: f"{item['meter']} ({item.get('vcpu','N/A')} vCPU, {item.get('memory','N/A')} GiB)" for item in instances_in_region}
            selected_instance_meter = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x), key=f'{service_type}_instance')
    elif service_type == 's3':
        with cols[1]:
            available_tiers = sorted(list(set(item['tier'] for item in RAW_DATA['s3'])))
            selected_tier = st.selectbox("Storage Tier", available_tiers, key='s3_tier')
        with cols[2]:
            storage_amount = st.number_input("Storage (GB)", min_value=1, value=1000, key='s3_gb')
    with cols[3]:
        st.session_state.quantity = st.number_input("Quantity", min_value=1, value=1, key='quantity_input')
    with cols[4]:
        st.write("") 
        st.write("") 
        if st.button("Compare Pricing", type="primary", use_container_width=True):
            if service_type in ['ec2', 'rds']:
                primary_instance = next((i for i in RAW_DATA[service_type] if i['region'] == selected_region and i['meter'] == selected_instance_meter), None)
                st.session_state.comparison_set = find_equivalent(primary_instance, service_type)
            elif service_type == 's3':
                st.session_state.comparison_set = get_s3_equivalents(selected_tier, storage_amount)

if st.session_state.comparison_set:
    results = st.session_state.comparison_set
    with st.container(border=True):
        st.header("Service Equivalency Mapping")
        if service_type in ['ec2', 'rds']:
            specs = ['Instance Type', 'vCPU', 'Memory', 'Region']
            table_data = {'Specification': specs}
            for cloud in ['azure', 'aws', 'gcp']:
                cloud_data = results.get(cloud, {})
                table_data[cloud.upper()] = [
                    cloud_data.get('meter', 'N/A'),
                    cloud_data.get('vcpu', 'N/A'),
                    f"{cloud_data.get('memory', 'N/A')} GiB",
                    cloud_data.get('region', 'N/A')
                ]
        else: # S3
            specs = ['Storage Tier', 'Region']
            table_data = {'Specification': specs}
            for cloud in ['azure', 'aws', 'gcp']:
                cloud_data = results.get(cloud, {})
                table_data[cloud.upper()] = [
                    cloud_data.get('tier', 'N/A'),
                    cloud_data.get('region', 'N/A')
                ]
        df = pd.DataFrame(table_data).set_index('Specification')
        st.table(df)

    with st.container(border=True):
        st.header("Pricing Comparison")
        cost_cols = st.columns(3)
        valid_costs = {cloud: data['cost'] for cloud, data in results.items() if data and 'cost' in data and pd.notna(data['cost'])}
        lowest_cost_cloud = min(valid_costs, key=valid_costs.get) if valid_costs else None
        cloud_map = {'azure': cost_cols[0], 'aws': cost_cols[1], 'gcp': cost_cols[2]}
        cloud_names = {'azure': 'Microsoft Azure', 'aws': 'Amazon AWS', 'gcp': 'Google Cloud'}
        for cloud, col in cloud_map.items():
            with col:
                data = results.get(cloud)
                if data and 'cost' in data and pd.notna(data['cost']):
                    total_cost = data['cost'] * st.session_state.quantity
                    st.subheader(cloud_names[cloud])
                    st.markdown(f"*{data.get('meter') or data.get('tier')}*")
                    st.metric(label=f"Total Monthly Cost (x{st.session_state.quantity})", value=f"${total_cost:,.2f}")
                    if cloud == lowest_cost_cloud:
                        st.success("✅ Recommended")
                else:
                    st.subheader(cloud_names[cloud])
                    st.markdown("*N/A*")
                    st.metric(label="Total Monthly Cost", value="N/A")

    with st.container(border=True):
        st.header("Cost Summary & Savings Analysis")
        summary_cols = st.columns(4)
        if valid_costs:
            costs = [c * st.session_state.quantity for c in valid_costs.values()]
            lowest = min(costs) if costs else 0
            average = sum(costs) / len(costs) if costs else 0
            monthly_savings = average - lowest
            with summary_cols[0]: st.metric("Lowest Cost", f"${lowest:,.2f}")
            with summary_cols[1]: st.metric("Average Cost", f"${average:,.2f}")
            with summary_cols[2]: st.metric("Monthly Savings", f"${monthly_savings:,.2f}")
            with summary_cols[3]: st.metric("Annual Savings", f"${monthly_savings * 12:,.2f}")
