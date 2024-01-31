package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Relay2MainContract contract for handling IoTDatas
type Relay2MainContract struct {
	contractapi.Contract
}

//toChaincodeArgs generates args for chaincode invoke
func toChaincodeArgs(args ...string) [][]byte {
	bargs := make([][]byte, len(args))
	for i, arg := range args {
		bargs[i] = []byte(arg)
	}
	return bargs
}


func (cc *Relay2MainContract) RetrieveIoTData(ctx CustomTransactionContextInterface, id string, newid string) error {
	
	queryArgs := toChaincodeArgs("GetIoTData", id)
	response := ctx.GetStub().InvokeChaincode("relayGeneralCC", queryArgs, "relay-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	if response.Payload == nil {
		return errors.New("InvokeChaincode returns nil!")
	}
	data := new(CompressedData)
	err := json.Unmarshal(response.Payload, data)
	if err != nil {
		return fmt.Errorf("Data retrieved from world state for key %s was not of type CompressedData", id)
	}
	

	writeArgs := toChaincodeArgs("NewIoTData", newid, data.From, data.Payload)
	response = ctx.GetStub().InvokeChaincode("mainGeneralCC", writeArgs, "main-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	return nil
}