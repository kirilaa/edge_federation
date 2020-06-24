// var HelloWorld = artifacts.require("HelloWorld");
var Federation = artifacts.require("Federation");
module.exports = function(deployer) {
    // deployer.deploy(HelloWorld);
    // Additional contracts can be deployed here
    deployer.deploy(Federation);
};