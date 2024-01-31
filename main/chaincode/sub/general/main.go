package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	subChainContract := new(SubChainContract)
    subChainContract.TransactionContextHandler = new(CustomTransactionContext)
    subChainContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(subChainContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}