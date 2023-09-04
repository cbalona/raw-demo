packages_to_load <- c(
    "SynthETIC",
    "plyr",
    "dplyr",
    "locfit",
    "actuar",
    "tidyr",
    "feather"
)

for (package_i in packages_to_load) {
  suppressPackageStartupMessages(
    library(
      package_i,
      character.only = TRUE
    )
  )
}
rm(package_i)

# simulate
setwd("IndividualClaimsSimulator")
source("Tools/functions simulation.r")

ref_claim <- 1              # currency is 1
time_unit <- 1/12           # we consider annual claims development
set_parameters(ref_claim=ref_claim, time_unit=time_unit)
years <- 10                 # number of occurrence years
I <- years/time_unit        # number of development periods

claims_list <- data.generation(seed=1000, future_info=FALSE)

write.csv(claims_list$claims, "/output/data/claims.csv")
write.csv(claims_list$paid, "/output/data/paid.csv")
