pragma solidity >0.7.0 <0.8.0;

contract Marketplace {
    address public doner;
    address public recipient;
    mapping (address => uint) public balances;

    event Donate(address doner, address recipient, uint amount);

    enum StateType {
          receiveDonation,
          needDonation
    }

    StateType public State;

    constructor() public {
        doner = msg.sender;
        State = StateType.needDonation;
    }
    
    function initAccount(address participant, uint amount) public{
        require(participant == msg.sender, "You cannot update other's account balances");
        require(balances[participant] == 0, "You can not add more money");
        balances[participant] = amount;
    }

    function donate(address doner, address recipient, uint amount) public payable {
        require(amount <= balances[doner], "Insufficient balance");
        State = StateType.receiveDonation;
        balances[doner] -= amount;
        balances[recipient] += amount;

        emit Donate(doner, recipient, balances[doner]);
    }
}
