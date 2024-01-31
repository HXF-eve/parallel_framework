package main

import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

func main(){
	main2RelayContract := new(Main2RelayContract)
    main2RelayContract.TransactionContextHandler = new(CustomTransactionContext)
    main2RelayContract.UnknownTransaction = UnknownTransactionHandler

	cc, err := contractapi.NewChaincode(main2RelayContract)

	if err != nil {
        panic(err.Error())
    }

    if err := cc.Start(); err != nil {
        panic(err.Error())
    }
}