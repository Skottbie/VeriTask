import hre from "hardhat";
const reg = await hre.ethers.getContractAt("VTRegistry","0xfB5Cd3bD07DC2c47E1464D002B122266A1b9e981");

for (let i = 1; i <= 3; i++) {
  try {
    const agent = await reg.getAgent(i);
    console.log(`Agent #${i}:`, {
      name: agent[0],
      creator: agent[1],
      wallet: agent[2],
      trustScore: agent[3].toString(),
      status: agent[4].toString(),
    });
  } catch (e) {
    console.log(`No agent #${i}`);
  }
}
