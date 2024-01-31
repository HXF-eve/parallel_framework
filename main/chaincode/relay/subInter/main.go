package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	sub2RelayContract := new(Sub2RelayContract)
    sub2RelayContract.TransactionContextHandler = new(CustomTransactionContext)
    sub2RelayContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(sub2RelayContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}