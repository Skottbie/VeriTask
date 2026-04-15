import hre from "hardhat";

const REGISTRY = "0xfB5Cd3bD07DC2c47E1464D002B122266A1b9e981";
const ONCHAINOS_WALLET = "0x430196e4cfe26267bd11c2a0c7a97b624da39472";
const ONCHAINOS_WALLET_ACCT3 = "0x0fecd525196a733f099e8d75af25fa6ff87ce10f";

async function main() {
  const reg = await hre.ethers.getContractAt("VTRegistry", REGISTRY);
  const target = process.argv[2] || ONCHAINOS_WALLET_ACCT3;

  console.log("devMode:", await reg.devMode());
  console.log("target:", target);
  console.log("whitelist before:", await reg.whitelist(target));

  const tx = await reg.addToWhitelist(target);
  const receipt = await tx.wait();

  console.log("whitelist after:", await reg.whitelist(target));
  console.log("tx:", tx.hash);
}

main().catch(console.error);
