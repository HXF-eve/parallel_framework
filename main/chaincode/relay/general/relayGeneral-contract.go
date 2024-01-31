package main

import (
	"encoding/json"
	"fmt"
	"errors"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// RelayReadContract contract for handling IoTDatas
type RelayReadContract struct {
	contractapi.Contract
}


func (cc *RelayReadContract) UploadIoTData(ctx CustomTransactionContextInterface, id string, from string, payload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing != nil {
		return fmt.Errorf("Cannot create new data in world state as key %s already exist", id)
	}

	data := new(CompressedData)
	data.From = from
	data.Payload = payload

	dataBytes, _ := json.Marshal(data)

	err := ctx.GetStub().PutState(id, []byte(dataBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

func (cc *RelayReadContract) UploadPKData(ctx CustomTransactionContextInterface, id string, payload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing != nil {
		return fmt.Errorf("Cannot create new data in world state as key %s already exist", id)
	}

	pk := new(PKData)
	
	pk.Payload = payload

	pkBytes, _ := json.Marshal(pk)

	err := ctx.GetStub().PutState(id, []byte(pkBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}


// GetIoTData returns the compressed iot data with id given from the world state
func (cc *RelayReadContract) GetIoTData(ctx CustomTransactionContextInterface, id string) (*CompressedData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	data := new(CompressedData)

	err := json.Unmarshal(existing, data)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}

	return data, nil
}

// GetPKData returns the pk data with id given from the world state
func (cc *RelayReadContract) GetPKData(ctx CustomTransactionContextInterface, id string) (*PKData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	data := new(PKData)

	err := json.Unmarshal(existing, data)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}

	return data, nil
}

func (cc *RelayReadContract) DeleteData(ctx CustomTransactionContextInterface, id string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	return ctx.GetStub().DelState(id)
}

// GetEvaluateTransactions returns functions of RelayReadContract not to be tagged as submit
func (cc *RelayReadContract) GetEvaluateTransactions() []string {
	return []string{"GetIoTData", "GetPKData"}
}